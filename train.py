# -*- coding: utf-8 -*-
# @Time    : 2020-02-26 17:44
# @Author  : Zonas
# @Email   : zonas.wang@gmail.com
# @File    : train.py
"""

"""
import argparse
import logging
import os
import os.path as osp
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
from torch.utils.data import DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from unet import NestedUNet
from unet import UNet
from utils.dataset import BasicDataset
from config import UNetConfig

from losses import LovaszLossSoftmax
from losses import LovaszLossHinge
from losses import dice_coeff
import pandas as pd

# from tool.functions import getExcel

cfg = UNetConfig()


def getExcel(features, excel_path, header=True):
    """保存values到excel文件中"""
    data = pd.DataFrame(features)
    writer = pd.ExcelWriter(excel_path)
    if header:
        data.to_excel(writer, 'page_1', float_format='%.5f')
    else:
        data.to_excel(writer, 'page_1', float_format='%.5f', header=False, index=False)
    writer.save()
    writer.close()


def train_net(net, cfg, path):
    dataset = BasicDataset(cfg.images_dir, cfg.masks_dir, cfg.scale)

    val_percent = cfg.validation / 100
    n_val = int(len(dataset) * val_percent)

    n_train = len(dataset) - n_val
    train, val = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train,
                              batch_size=cfg.batch_size,  # TODO:set to smaller
                              shuffle=True,
                              num_workers=0,  # TODO:set to 0
                              pin_memory=True)
    val_loader = DataLoader(val,
                            batch_size=cfg.batch_size,  # TODO:set to smaller
                            shuffle=False,
                            num_workers=0,  # TODO:set to 0
                            pin_memory=True)

    writer = SummaryWriter(comment=f'LR_{cfg.lr}_BS_{cfg.batch_size}_SCALE_{cfg.scale}')
    global_step = 0

    logging.info(f'''Starting training:
        Epochs:          {cfg.epochs}
        Batch size:      {cfg.batch_size}
        Learning rate:   {cfg.lr}
        Optimizer:       {cfg.optimizer}
        Training size:   {n_train}
        Validation size: {n_val}
        Checkpoints:     {cfg.save_cp}
        Device:          {device.type}
        Images scaling:  {cfg.scale}
    ''')

    if cfg.optimizer == 'Adam':
        optimizer = optim.Adam(net.parameters(),
                               lr=cfg.lr)
    elif cfg.optimizer == 'RMSprop':
        optimizer = optim.RMSprop(net.parameters(),
                                  lr=cfg.lr,
                                  weight_decay=cfg.weight_decay)
    else:
        optimizer = optim.SGD(net.parameters(),
                              lr=cfg.lr,
                              momentum=cfg.momentum,
                              weight_decay=cfg.weight_decay,
                              nesterov=cfg.nesterov)

    scheduler = optim.lr_scheduler.MultiStepLR(optimizer,
                                               milestones=cfg.lr_decay_milestones,
                                               gamma=cfg.lr_decay_gamma)
    if cfg.n_classes > 1:
        criterion = LovaszLossSoftmax()  # 基于IOU的损失函数lovaszSoftmax
    else:
        criterion = LovaszLossHinge()

    best_loss = float("inf")
    train_loss_value, val_loss_value = [], []

    for epoch in range(cfg.epochs):
        net.train()
        n, train_loss = 0.0, 0.0
        epoch_loss = 0
        with tqdm(total=n_train, desc=f'Epoch {epoch + 1}/{cfg.epochs}', unit='img') as pbar:
            for batch in train_loader:
                batch_imgs = batch['image']
                batch_masks = batch['mask']
                assert batch_imgs.shape[1] == cfg.n_channels, \
                    f'Network has been defined with {cfg.n_channels} input channels, ' \
                    f'but loaded images have {batch_imgs.shape[1]} channels. Please check that ' \
                    'the images are loaded correctly.'

                batch_imgs = batch_imgs.to(device=device, dtype=torch.float32)
                mask_type = torch.float32 if cfg.n_classes == 1 else torch.long
                batch_masks = batch_masks.to(device=device, dtype=mask_type)

                inference_masks = net(batch_imgs)

                if cfg.n_classes == 1:
                    inferences = inference_masks.squeeze(1)
                    masks = batch_masks.squeeze(1)
                else:
                    inferences = inference_masks
                    masks = batch_masks

                if cfg.deepsupervision:
                    loss = 0
                    for inference_mask in inferences:  # TODO: why not one image?
                        loss += criterion(inference_mask, masks)
                    loss /= len(inferences)
                else:
                    loss = criterion(inferences, masks)
                # __________________________________
                if loss < best_loss:
                    best_loss = loss
                    torch.save(net.state_dict(), path+"/bestmodel.pth")

                epoch_loss += loss.item()
                n += masks.shape[0]

                # __________________________________
                # epoch_loss += loss.item()
                writer.add_scalar('Loss/train', loss.item(), global_step)
                writer.add_scalar('model/lr', optimizer.param_groups[0]['lr'], global_step)
                # 设置进度条右边显示的信息
                pbar.set_postfix(**{'loss (batch)': loss.item()})

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                scheduler.step()

                pbar.update(batch_imgs.shape[0])
                global_step += 1

                if global_step % (len(dataset) // (10 * cfg.batch_size)) == 0:
                    val_score = eval_net(net, val_loader, device, n_val, cfg)
                    if cfg.n_classes > 1:
                        logging.info('Validation cross entropy: {}'.format(val_score))
                        writer.add_scalar('CrossEntropy/test', val_score, global_step)
                    else:
                        logging.info('Validation Dice Coeff: {}'.format(val_score))
                        writer.add_scalar('Dice/test', val_score, global_step)

                    writer.add_images('images', batch_imgs, global_step)
                    if cfg.deepsupervision:
                        inference_masks = inference_masks[-1]
                    if cfg.n_classes == 1:
                        # writer.add_images('masks/true', batch_masks, global_step)
                        inference_mask = torch.sigmoid(inference_masks) > cfg.out_threshold
                        writer.add_images('masks/inference',
                                          inference_mask,
                                          global_step)
                    else:
                        # writer.add_images('masks/true', batch_masks, global_step)
                        ids = inference_masks.shape[1]  # N x C x H x W
                        inference_masks = torch.chunk(inference_masks, ids, dim=1)  # torch.chunk是按列切割成ids个
                        for idx in range(0, len(inference_masks)):
                            inference_mask = torch.sigmoid(inference_masks[idx]) > cfg.out_threshold
                            writer.add_images('masks/inference_' + str(idx),
                                              inference_mask,
                                              global_step)
            train_loss = epoch_loss / n
            train_loss_value.append(train_loss)
            val_loss_value.append(val_score)

        excel_path1 = path + '/train_loss.xlsx'
        getExcel(train_loss_value, excel_path1, header=False)

        excel_path2 = path + '/val_loss.xlsx'
        getExcel(val_loss_value, excel_path2, header=False)

        if cfg.save_cp:
            try:
                checkpoints_path =path + "/checkpoints"
                os.makedirs(checkpoints_path)
                logging.info('Created checkpoints directory')
            except OSError:
                pass

            ckpt_name = 'epoch_' + str(epoch + 1) + '.pth'
            torch.save(net.state_dict(),
                       osp.join(checkpoints_path, ckpt_name))
            logging.info(f'Checkpoint {epoch + 1} saved !')

    writer.close()


def eval_net(net, loader, device, n_val, cfg):
    """
    Evaluation without the densecrf with the dice coefficient
    """
    net.eval()
    tot = 0

    with tqdm(total=n_val, desc='Validation round', unit='img', leave=False) as pbar:
        for batch in loader:
            imgs = batch['image']
            true_masks = batch['mask']

            imgs = imgs.to(device=device, dtype=torch.float32)
            mask_type = torch.float32 if cfg.n_classes == 1 else torch.long
            true_masks = true_masks.to(device=device, dtype=mask_type)

            # compute loss
            if cfg.deepsupervision:
                masks_preds = net(imgs)
                loss = 0
                for masks_pred in masks_preds:
                    tot_cross_entropy = 0
                    for true_mask, pred in zip(true_masks, masks_pred):
                        pred = (pred > cfg.out_threshold).float()
                        if cfg.n_classes > 1:
                            sub_cross_entropy = F.cross_entropy(pred.unsqueeze(dim=0),
                                                                true_mask.unsqueeze(dim=0).squeeze(1)).item()
                        else:
                            sub_cross_entropy = dice_coeff(pred, true_mask.squeeze(dim=1)).item()
                        tot_cross_entropy += sub_cross_entropy
                    tot_cross_entropy = tot_cross_entropy / len(masks_preds)
                    tot += tot_cross_entropy
            else:
                masks_pred = net(imgs)
                for true_mask, pred in zip(true_masks, masks_pred):
                    pred = (pred > cfg.out_threshold).float()
                    if cfg.n_classes > 1:
                        tot += F.cross_entropy(pred.unsqueeze(dim=0), true_mask.unsqueeze(dim=0).squeeze(1)).item()
                    else:
                        tot += dice_coeff(pred, true_mask.squeeze(dim=1)).item()

            pbar.update(imgs.shape[0])

    return tot / n_val


if __name__ == '__main__':
    check_dir = lambda d: None if os.path.exists(d) else os.makedirs(d)

    time_str= time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    train_path="./data/result/"+time_str
    check_dir(train_path)

    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # logging.basicConfig(level=logging.INFO, format=log_format)  # TODO: 修改每次log文件名
    logging.basicConfig(filename=train_path+"/logging.log", level=logging.INFO, format=log_format)  # TODO: 修改每次log文件名
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')  # logging 日志输出

    net = eval(cfg.model)(cfg)  # 相当于：net=NestedUNet(cfg) 将"NestedUNet"去掉双引号，变成相应的类名
    logging.info(f'Network:\n'
                 f'\t{cfg.model} model\n'
                 f'\t{cfg.n_channels} input channels\n'
                 f'\t{cfg.n_classes} output channels (classes)\n'
                 f'\t{"Bilinear" if cfg.bilinear else "Dilated conv"} upscaling')

    # pre-training model
    if cfg.load:
        net.load_state_dict(
            torch.load(cfg.load, map_location=device)
        )
        logging.info(f'Model loaded from {cfg.load}')

    net.to(device=device)
    # faster convolutions, but more memory
    # cudnn.benchmark = True

    try:
        train_net(net=net, cfg=cfg, path=train_path)
    except KeyboardInterrupt:
        '''
        命令行程序运行期间，如果用户想终止程序，一般都会采用Ctrl-C快捷键，这个快捷键会引发python程序抛出KeyboardInterrupt异常。
        我们可以捕获这个异常，在用户按下Ctrl-C的时候，进行一些清理工作。
        '''
        torch.save(net.state_dict(), 'INTERRUPTED.pth')
        logging.info('Saved interrupt')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
