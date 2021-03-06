import torch
from torch.nn.modules.module import Module
from torch.nn.parameter import Parameter
from collections import OrderedDict

class FlexModule(Module):
    """sub-class for flexible module implementation
    """
    def __init__(self):
        super(FlexModule, self).__init__()
        self._nonleaf_parameters = OrderedDict()
        self.shapes = OrderedDict()

    def register_nonleaf_parameter(self, name, param):
        r"""Adds a parameter to the module.
        The parameter can be accessed as an attribute using given name.
        Args:
            name (string): name of the parameter. The parameter can be accessed
                from this module using the given name
            parameter (Parameter): parameter to be added to the module.
        """
        if '_nonleaf_parameters' not in self.__dict__:
            raise AttributeError(
                "cannot assign nonleaf parameter before FlexModule.__init__() call")

        elif not isinstance(name, torch._six.string_classes):
            raise TypeError("nonleaf parameter name should be a string. "
                            "Got {}".format(torch.typename(name)))
        elif '.' in name:
            raise KeyError("nonleaf parameter name can't contain \".\"")
        elif name == '':
            raise KeyError("nonleaf parameter name can't be empty string \"\"")
        elif hasattr(self, name) and name not in self._nonleaf_parameters:
            raise KeyError("attribute '{}' already exists".format(name))
        elif param is not None and not isinstance(param, torch.Tensor):
            raise TypeError("cannot assign '{}' object to nonleaf parameter '{}' "
                            "(torch Tensor or None required)"
                            .format(torch.typename(param), name))

        self._nonleaf_parameters[name] = param

    def __getattr__(self, name):
        if '_parameters' in self.__dict__:
            _parameters = self.__dict__['_parameters']
            if name in _parameters:
                return _parameters[name]
        if '_nonleaf_parameters' in self.__dict__:
            _nonleaf_parameters = self.__dict__['_nonleaf_parameters']
            if name in _nonleaf_parameters:
                return _nonleaf_parameters[name]
        if '_buffers' in self.__dict__:
            _buffers = self.__dict__['_buffers']
            if name in _buffers:
                return _buffers[name]
        if '_modules' in self.__dict__:
            modules = self.__dict__['_modules']
            if name in modules:
                return modules[name]
        raise AttributeError("'{}' object has no attribute '{}'".format(
            type(self).__name__, name))

    def __setattr__(self, name, value):
        def remove_from(*dicts):
            for d in dicts:
                if name in d:
                    del d[name]

        params = self.__dict__.get('_parameters')
        if isinstance(value, Parameter):
            if params is None:
                raise AttributeError(
                    "cannot assign parameters before Module.__init__() call")
            remove_from(self.__dict__, self._buffers, self._modules)
            self.register_parameter(name, value)
        elif params is not None and name in params:
            if value is not None and not (isinstance(value, torch.Tensor) and value.is_leaf is False):
                raise TypeError("cannot assign '{}' as parameter '{}' "
                                "(torch.nn.Parameter, non-leaf torch.Tensor or None expected)"
                                .format(torch.typename(value), name))
            self.register_parameter(name, value)
        else:
            modules = self.__dict__.get('_modules')
            if isinstance(value, Module):
                if modules is None:
                    raise AttributeError(
                        "cannot assign module before Module.__init__() call")
                remove_from(self.__dict__, self._parameters, self._buffers)
                modules[name] = value
            elif modules is not None and name in modules:
                if value is not None:
                    raise TypeError("cannot assign '{}' as child module '{}' "
                                    "(torch.nn.Module or None expected)"
                                    .format(torch.typename(value), name))
                modules[name] = value
            else:
                buffers = self.__dict__.get('_buffers')
                if buffers is not None and name in buffers:
                    if value is not None and not isinstance(value, torch.Tensor):
                        raise TypeError("cannot assign '{}' as buffer '{}' "
                                        "(torch.Tensor or None expected)"
                                        .format(torch.typename(value), name))
                    buffers[name] = value
                else:
                    nonleaf_parameters = self.__dict__.get('_nonleaf_parameters')
                    if nonleaf_parameters is not None and name in nonleaf_parameters:
                        if value is not None and not isinstance(value, torch.Tensor):
                            raise TypeError("cannot assign '{}' as nonleaf parameter '{}' "
                                            "(torch.Tensor or None expected)"
                                            .format(torch.typename(value), name))
                        nonleaf_parameters[name] = value
                    else:
                        object.__setattr__(self, name, value)

    def named_nonleaf_parameters(self, prefix='', recurse=True):
        gen = self._named_members(
            lambda module: module._nonleaf_parameters.items(),
            prefix=prefix, recurse=recurse)
        for elem in gen:
            yield elem

    def nonleaf_parameters(self, recurse=True):
        for name, param in self.named_nonleaf_parameters(recurse=recurse):
            yield param