# Video-Classification-Pytorch

*Still in development*.

This is a repository containing 3D models and 2D models for video classification based on [TSN Pytorch Codebase](https://github.com/yjxiong/tsn-pytorch)

## Training

Write a customized script like
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python main.py \
kinetics400 \
data/kinetics400/kinetics_train_list.txt \
data/kinetics400/kinetics_val_list.txt \
--arch resnet50_3d \
--dro 0.2 \
--mode 3D \
--t_length 16 \
--t_stride 4 \
--pretrained \
--epochs 95 \
--batch-size 64 \
--lr 0.001 \
--lr_steps 40 80 90 \
--workers 32 \
```

## Testing
Write a customized script like
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python ./test.py \
kinetics400 \
data/kinetics400/kinetics_val_list.txt \
./output/kinetics400_resnet50_3d_3D_length16_stride4_dropout0.2/model_best.pth \
--arch resnet50_3d \
--mode TSN+3D \
--batch_size 2 \
--num_segments 15 \
--test_crops 10 \
--t_length 16 \
--t_stride 4 \
--crop_fusion_type max \
--dropout 0.2 \
--workers 12 \
--save_scores ./output/kinetics400_resnet50_3d_3D_length16_stride4_dropout0.2
```
