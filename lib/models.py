import os
from torch import nn
from torch.nn.parameter import Parameter
from .networks.mnet2 import mnet2
from .networks.mnet2_3d import mnet2_3d
from .networks.resnet import *
from .networks.resnet_3d import *
from .networks.shadownet import resnet50_shadow

from .transforms import *

import ipdb

class VideoModule(nn.Module):
    def __init__(self, num_class, base_model_name='resnet50', 
                 before_softmax=True, dropout=0.8, pretrained=True, pretrained_model=None):
        super(VideoModule, self).__init__()
        self.num_class = num_class
        self.base_model_name = base_model_name
        self.before_softmax = before_softmax
        self.dropout = dropout
        self.pretrained = pretrained
        self.pretrained_model = pretrained_model

        self._prepare_base_model(base_model_name)

        if not self.before_softmax:
            self.softmax = nn.Softmax()

    def _prepare_base_model(self, base_model_name):
        """
        base_model+(dropout)+classifier
        """
        base_model_dict = None
        classifier_dict = None
        if self.pretrained and self.pretrained_model:
            model_dict = torch.load(self.pretrained_model)
            base_model_dict = {k: v for k, v in model_dict.items() if "classifier" not in k}
            classifier_dict = {'.'.join(k.split('.')[1:]): v for k, v in model_dict.items() if "classifier" in k}
        # base model
        if "resnet" in base_model_name:
            self.base_model = eval(base_model_name)(pretrained=self.pretrained, \
                                   feat=True, pretrained_model=base_model_dict)
        elif base_model_name == "mnet2":
            model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "../models/mobilenet_v2.pth.tar")
            self.base_model = mnet2(pretrained=model_path, feat=True)
        elif base_model_name == "mnet2_3d":
            model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "../models/mobilenet_v2.pth.tar")
            self.base_model = mnet2_3d(pretrained=model_path, feat=True)
        else:
            raise ValueError('Unknown base model: {}'.format(base_model))

        # classifier: (dropout) + fc
        if self.dropout == 0:
            self.classifier = nn.Linear(self.base_model.feat_dim, self.num_class)
        elif self.dropout > 0:
            self.classifier = nn.Sequential(nn.Dropout(self.dropout), nn.Linear(self.base_model.feat_dim, self.num_class))

        # init classifier
        for m in self.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='linear')
                nn.init.constant_(m.bias, 0)
        
        if self.pretrained and self.pretrained_model:
            pass
            # print("load classifier")
            # self.classifier.load_state_dict(classifier_dict)

    def forward(self, input):
        out = self.base_model(input)
        out = self.classifier(out)

        if not self.before_softmax:
            out = self.softmax(out)

        return out

    def get_augmentation(self):
        return torchvision.transforms.Compose([GroupMultiScaleCrop(input_size=224, scales=[1, .875, .75, .66]),
                                                   GroupRandomHorizontalFlip()])

class VideoShadowModule(nn.Module):
    def __init__(self, num_class, base_model_name='resnet50_3d', 
                 before_softmax=True, dropout=0.8, pretrained=True, pretrained_model=None):
        super(VideoShadowModule, self).__init__()
        self.num_class = num_class
        self.base_model_name = base_model_name
        self.before_softmax = before_softmax
        self.dropout = dropout
        self.pretrained = pretrained
        self.pretrained_model = pretrained_model

        self._prepare_base_model(base_model_name)
        self.shadow_model_name = base_model_name.split('_')[0] + '_shadow'

        if not self.before_softmax:
            self.softmax = nn.Softmax()

    def _prepare_base_model(self, base_model_name):
        """
        base_model+(dropout)+classifier
        """
        base_model_dict = None
        classifier_dict = None
        if self.pretrained and self.pretrained_model:
            model_dict = torch.load(self.pretrained_model)
            base_model_dict = {k: v for k, v in model_dict.items() if "classifier" not in k}
            classifier_dict = {'.'.join(k.split('.')[1:]): v for k, v in model_dict.items() if "classifier" in k}
        # base model
        if "resnet" in base_model_name:
            self.base_model = eval(base_model_name)(pretrained=self.pretrained, \
                                   feat=True, pretrained_model=base_model_dict)
        elif base_model_name == "mnet2":
            model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "../models/mobilenet_v2.pth.tar")
            self.base_model = mnet2(pretrained=model_path, feat=True)
        elif base_model_name == "mnet2_3d":
            model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "../models/mobilenet_v2.pth.tar")
            self.base_model = mnet2_3d(pretrained=model_path, feat=True)
        else:
            raise ValueError('Unknown base model: {}'.format(base_model))

        # classifier: (dropout) + fc
        if self.dropout == 0:
            self.classifier = nn.Linear(self.base_model.feat_dim, self.num_class)
            self.shadow_classifier = nn.Linear(self.base_model.feat_dim, self.num_class)
        elif self.dropout > 0:
            self.classifier = nn.Sequential(nn.Dropout(self.dropout), nn.Linear(self.base_model.feat_dim, self.num_class))
            self.shadow_classifier = nn.Sequential(nn.Dropout(self.dropout), nn.Linear(self.base_model.feat_dim, self.num_class))

        # shadow controller
        # self.controller = Parameter(torch.ones(1))

        # init classifier
        for m in self.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='linear')
                nn.init.constant_(m.bias, 0)

        for m in self.shadow_classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='linear')
                nn.init.constant_(m.bias, 0)
        
        # if self.pretrained and self.pretrained_model:
            # print("load classifier")
            # self.classifier.load_state_dict(classifier_dict)

    def _prepare_shadow_model(self):
        # shadow model (currently only support resnet50_shadow)
        if "resnet" in self.shadow_model_name:
            self.shadow_model = eval(self.shadow_model_name)(feat=True)
        else:
            raise ValueError('Unknown shadow model: {}'.format())

    def _cast_shadow(self):
        shadow_modules_dict = dict(self.shadow_model.named_modules())
        shadow_module_names = shadow_modules_dict.keys()

        # cast parameters
        for param_base in self.base_model.named_parameters():
            name = param_base[0]
            param = param_base[1]
            _items = name.split('.')
            module_name = '.'.join(_items[:-1])
            param_name = _items[-1]
            assert(param_name in ('weight', 'bias')), "parameter type must be weight or bias"
            assert(module_name in shadow_module_names),"Name not in shadow_module_names"
            # casting
            shadow_module = shadow_modules_dict[module_name]
            if param.dim() == 5 and param.shape[2] != 1:
                param = param.sum(dim=2, keepdim=True) #.detach()
            # else:
            #     param = param #.detach()
            assert(param.shape == shadow_module.shapes[param_name]), "param shape mismatch"
            shadow_module.register_nonleaf_parameter(param_name, param)

        # cast buffers
        for buffer_base in self.base_model.named_buffers():
            name = buffer_base[0]
            buffer = buffer_base[1].detach().clone()
            _items = name.split('.')
            module_name = '.'.join(_items[:-1])
            buffer_name = _items[-1]
            assert(buffer_name in ('running_mean', 'running_var', 'num_batches_tracked')), "buffer type constrain"
            assert(module_name in shadow_module_names), "Name not in shadow_module_names"
            # casting
            shadow_module = shadow_modules_dict[module_name]
            # if shadow_module.shapes[buffer_name] == :
                # print(buffer_name, buffer.shape, shadow_module.shapes[buffer_name])
            # assert(buffer.shape == shadow_module.shapes[buffer_name]), "buffer shape mismatch"
            shadow_module.register_buffer(buffer_name, buffer)

    def _aggregate(self, sparse_pred):
        # assert(dense_pred.dim() == 2 and sparse_pred.dim() == 3), "Prediction dimension error."
        assert(sparse_pred.dim() == 3), "Prediction dimension error."
        # dense_pred = dense_pred.view(dense_pred.shape[0], dense_pred.shape[1], 1)
        # out = torch.cat((dense_pred, sparse_pred * 0.5), dim=2)
        # out = dense_pred
        # out = sparse_pred
        num_segments = sparse_pred.shape[2]
        # print("Num Segment: ", num_segments)
        out = sparse_pred.sum(dim=2, keepdim=False).div(num_segments)
        return out

    def forward(self, input):
        base_input = input[:,:,:16,...]
        # Infer 3D network
        # print("<--device: {} | befor forward conv1.weight: {}-->\n".format(input.device, self.base_model.conv1.weight[:10,0,0,0,0]))
        # print("<--device: {} | befor forward bn1.running_mean: {}-->\n".format(input.device, self.base_model.bn1.running_mean[:10]))
        out_base = self.base_model(base_input)
        out = self.classifier(out_base)
        if not self.before_softmax:
            out = self.softmax(out)
        # print("<--device: {} | after forward conv1.weight: {}-->\n".format(input.device, self.base_model.conv1.weight[:10,0,0,0,0]))
        # print("<--device: {} | after forward bn1.running_mean: {}-->\n".format(input.device, self.base_model.bn1.running_mean[:10]))
        if input.shape[2] > 16:
            self._prepare_shadow_model()
            shadow_input = input[:,:,16:,...]
            # Cast Shadow
            self._cast_shadow()
            # Infer TSN
            out_shadow = self.shadow_model(shadow_input)
            # Aggregate across segments
            out_2 = self._aggregate(out_shadow)
            out_2 = self.classifier(out_2)
            if not self.before_softmax:
                out_2 = self.softmax(out_2)
            return out, out_2
        else:
            return out

    def get_augmentation(self):
        return torchvision.transforms.Compose([GroupMultiScaleCrop(input_size=224, scales=[1, .875, .75, .66]),
                                                   GroupRandomHorizontalFlip()])


class TSN(nn.Module):
    """Temporal Segment Network
    
    """
    def __init__(self, batch_size, video_module, num_segments=1, t_length=1, 
                 crop_fusion_type='max', mode="3D"):
        super(TSN, self).__init__()
        self.t_length = t_length
        self.batch_size = batch_size
        self.num_segments = num_segments
        self.video_module = video_module
        self.crop_fusion_type = crop_fusion_type
        self.mode = mode

    def forward(self, input):
        # reshape input first
        shape = input.shape
        if "3D" in self.mode:
            assert(len(shape)) == 5, "In 3D mode, input must have 5 dims."
            shape = (shape[0], shape[1], shape[2]//self.t_length, self.t_length) + shape[3:]
            input = input.view(shape).permute((0, 2, 1, 3, 4, 5)).contiguous()
            shape = (input.shape[0] * input.shape[1], ) + input.shape[2:]
            input = input.view(shape)
        elif "2D" in self.mode:
            assert(len(shape)) == 4, "In 2D mode, input must have 4 dims."
            shape = (shape[0]*shape[1]//3, 3,) + shape[2:]
            input = input.view(shape)
        else:
            raise Exception("Unsupported mode.")

        # base network forward
        output = self.video_module(input)
        # fuse output
        output = output.view((self.batch_size, 
                              output.shape[0] // (self.batch_size * self.num_segments), 
                              self.num_segments, output.shape[1]))
        if self.crop_fusion_type == 'max':
            # pdb.set_trace()
            output = output.max(1)[0].squeeze(1)
        elif self.crop_fusion_type == 'avg':
            output = output.mean(1).squeeze(1)
        pred = output.mean(1).squeeze(1)
        return (output, pred)
