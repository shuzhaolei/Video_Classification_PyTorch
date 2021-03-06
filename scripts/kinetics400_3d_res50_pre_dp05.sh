# CUDA_LAUNCH_BLOCKING=1 \
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
python main.py \
kinetics400 \
data/kinetics400/kinetics_train_list.txt \
data/kinetics400/kinetics_val_list.txt \
--arch resnet50_3d \
--dro 0.5 \
--mode 3D \
--t_length 16 \
--t_stride 4 \
--pretrained \
--epochs 100 \
--batch-size 64 \
--lr 0.001 \
--lr_steps 40 80 90 \
--workers 32 \
--resume output/kinetics400_resnet50_3d_3D_length16_stride4_dropout0.5/checkpoint_95epoch.pth
