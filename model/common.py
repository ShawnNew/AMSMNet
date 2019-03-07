import math

import torch
import torch.nn as nn
import torch.nn.functional as F

def default_conv(in_channels, out_channels, kernel_size, bias=True):
    return nn.Conv2d(
        in_channels, out_channels, kernel_size,
        padding=(kernel_size//2), bias=bias)

class MeanShift(nn.Conv2d):
    def __init__(
        self, rgb_range,
        rgb_mean=(0.4488, 0.4371, 0.4040), rgb_std=(1.0, 1.0, 1.0), sign=-1):

        super(MeanShift, self).__init__(3, 3, kernel_size=1)
        std = torch.Tensor(rgb_std)
        self.weight.data = torch.eye(3).view(3, 3, 1, 1) / std.view(3, 1, 1, 1)
        self.bias.data = sign * rgb_range * torch.Tensor(rgb_mean) / std
        for p in self.parameters():
            p.requires_grad = False

class BasicBlock(nn.Sequential):
    def __init__(
        self, conv, in_channels, out_channels, kernel_size, stride=1, bias=False,
        bn=True, act=nn.ReLU(True)):

        m = [conv(in_channels, out_channels, kernel_size, bias=bias)]
        if bn:
            m.append(nn.BatchNorm2d(out_channels))
        if act is not None:
            m.append(act)

        super(BasicBlock, self).__init__(*m)

class ResBlock(nn.Module):
    def __init__(
        self, conv, n_feats, kernel_size,
        bias=True, bn=False, act=nn.ReLU(True), res_scale=1):

        super(ResBlock, self).__init__()
        m = []
        for i in range(2):
            m.append(conv(n_feats, n_feats, kernel_size, bias=bias))
            if bn:
                m.append(nn.BatchNorm2d(n_feats))
            if i == 0:
                m.append(act)

        self.body = nn.Sequential(*m)
        self.res_scale = res_scale

    def forward(self, x):
        res = self.body(x).mul(self.res_scale)
        res += x

        return res

class PreResBlock(nn.Module):
    def __init__(
        self, conv, in_channels, out_channels, kernel_size,
        bias=True, bn=False, act=nn.ReLU(True), res_scale=1):

        super(PreResBlock, self).__init__()
        m_1 = []
        m_1.append(conv(in_channels, out_channels, kernel_size, bias=bias))
        m_1.append(nn.BatchNorm2d(out_channels))
        m_1.append(act)
        m_2 = []
        m_2.append(conv(out_channels, out_channels, kernel_size, bias=bias))
        m_2.append(nn.BatchNorm2d(out_channels))
        self.body_1 = nn.Sequential(*m_1)
        self.body_2 = nn.Sequential(*m_2)
        self.res_scale = res_scale

    def forward(self, x):
        x = self.body_1(x)
        res = self.body_2(x).mul(self.res_scale)
        res += x
        return res


class Upsampler(nn.Sequential):
    def __init__(self, conv, n_feats, bn=False, act=False, bias=True):

        m = []
        m.append(conv(n_feats, 4 * n_feats, 3, bias))
        m.append(nn.PixelShuffle(2))
        if bn:
            m.append(nn.BatchNorm2d(n_feats))
        if act == 'relu':
            m.append(nn.ReLU(True))
        elif act == 'prelu':
            m.append(nn.PReLU(n_feats))

        super(Upsampler, self).__init__(*m)
