#!/usr/bin/env python3
"""Minimal PyTorch runner for the official Real-ESRGAN architectures.

The upstream ``realesrgan``/``basicsr`` packages do not install cleanly on
Python 3.13, so this module vendors only the two model definitions and the
tiled inference needed for video frames. It is intentionally dependency-light
(torch + numpy + Pillow) and keeps the upstream licenses:

- SRVGGNetCompact: Real-ESRGAN, BSD-3-Clause
  https://github.com/xinntao/Real-ESRGAN/blob/master/realesrgan/archs/srvgg_arch.py
- RRDBNet: BasicSR, Apache-2.0
  https://github.com/XPixelGroup/BasicSR/blob/master/basicsr/archs/rrdbnet_arch.py

Checkpoints are never downloaded here. Pass verified weights explicitly and
record their source and hash next to them.
"""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

MODELS = {
    "realesr-general-x4v3": {"arch": "srvgg", "scale": 4, "num_conv": 32},
    "RealESRGAN_x2plus": {"arch": "rrdb", "scale": 2, "num_block": 23},
    "RealESRGAN_x4plus": {"arch": "rrdb", "scale": 4, "num_block": 23},
    "RealESRNet_x4plus": {"arch": "rrdb", "scale": 4, "num_block": 23},
}


class SRVGGNetCompact(nn.Module):
    """Compact VGG-style super-resolution network (Real-ESRGAN)."""

    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16,
                 upscale=4, act_type="prelu"):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList()
        self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
        self.body.append(nn.PReLU(num_parameters=num_feat))
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")


def _pixel_unshuffle(x, scale):
    batch, channel, height, width = x.size()
    out_channel = channel * (scale ** 2)
    height //= scale
    width //= scale
    view = x.view(batch, channel, height, scale, width, scale)
    return view.permute(0, 1, 3, 5, 2, 4).reshape(batch, out_channel, height, width)


def _make_layer(block, count, **kwargs):
    return nn.Sequential(*[block(**kwargs) for _ in range(count)])


def _default_init(modules, scale=1, bias_fill=0):
    for module in modules:
        for layer in module.modules():
            if isinstance(layer, nn.Conv2d):
                nn.init.kaiming_normal_(layer.weight, a=0, mode="fan_in",
                                        nonlinearity="relu")
                layer.weight.data *= scale
                if layer.bias is not None:
                    layer.bias.data.fill_(bias_fill)


class ResidualDenseBlock(nn.Module):
    def __init__(self, num_feat=64, num_grow_ch=32):
        super().__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)
        _default_init([self.conv1, self.conv2, self.conv3, self.conv4,
                       self.conv5], 0.1)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, num_feat, num_grow_ch=32):
        super().__init__()
        self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, scale=4, num_feat=64,
                 num_block=23, num_grow_ch=32):
        super().__init__()
        self.scale = scale
        if scale == 2:
            num_in_ch *= 4
        elif scale == 1:
            num_in_ch *= 16
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = _make_layer(RRDB, num_block, num_feat=num_feat,
                                num_grow_ch=num_grow_ch)
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        if self.scale == 2:
            feat = _pixel_unshuffle(x, 2)
        elif self.scale == 1:
            feat = _pixel_unshuffle(x, 4)
        else:
            feat = x
        feat = self.conv_first(feat)
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2,
                                                      mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2,
                                                      mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


def _state(path: str) -> dict:
    data = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(data, dict):
        if "params_ema" in data:
            data = data["params_ema"]
        elif "params" in data:
            data = data["params"]
    if not isinstance(data, dict):
        raise RuntimeError(f"unrecognised checkpoint: {path}")
    return {key.removeprefix("module."): value for key, value in data.items()}


def load_model(model: str, weights: str, weights2: str | None = None,
               denoise_strength: float | None = None):
    if model not in MODELS:
        raise RuntimeError(f"unsupported pytorch model: {model}")
    spec = MODELS[model]
    if spec["arch"] == "srvgg":
        net = SRVGGNetCompact(num_conv=spec["num_conv"], upscale=spec["scale"])
    else:
        net = RRDBNet(scale=spec["scale"], num_block=spec["num_block"])
    state = _state(weights)
    if weights2 and denoise_strength is not None:
        other = _state(weights2)
        weight = min(1.0, max(0.0, float(denoise_strength)))
        state = {key: (1.0 - weight) * value + weight * other[key]
                 for key, value in state.items() if key in other}
    net.load_state_dict(state, strict=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    net = net.to(device).eval()
    if device == "cuda":
        net = net.half()
    return net, device


def _mod_pad(x, multiple):
    height, width = x.shape[-2:]
    pad_h = (multiple - height % multiple) % multiple
    pad_w = (multiple - width % multiple) % multiple
    if pad_h or pad_w:
        x = F.pad(x, (0, pad_w, 0, pad_h), mode="reflect")
    return x, pad_h, pad_w


def _tiled(net, x, scale, tile, tile_pad):
    height, width = x.shape[-2:]
    if not tile or (tile >= height and tile >= width):
        return net(x)
    output = x.new_zeros((1, 3, height * scale, width * scale))
    for top in range(0, height, tile):
        for left in range(0, width, tile):
            y0, x0 = max(0, top - tile_pad), max(0, left - tile_pad)
            y1 = min(height, top + tile + tile_pad)
            x1 = min(width, left + tile + tile_pad)
            patch = x[:, :, y0:y1, x0:x1]
            produced = net(patch)
            oy = (top - y0) * scale
            ox = (left - x0) * scale
            bottom, right = min(height, top + tile), min(width, left + tile)
            output[:, :, top * scale:bottom * scale,
                   left * scale:right * scale] = produced[
                       :, :, oy:oy + (bottom - top) * scale,
                       ox:ox + (right - left) * scale]
    return output


def enhance(net, device: str, image: torch.Tensor, outscale: int,
            tile: int = 256, tile_pad: int = 10) -> torch.Tensor:
    """Run one RGB tensor (1x3xHxW, 0..1) and return the requested scale."""
    net_scale = net.upscale if isinstance(net, SRVGGNetCompact) else net.scale
    mod = 2 if net_scale == 2 else 1
    image, pad_h, pad_w = _mod_pad(image, mod)
    half = next(net.parameters()).dtype == torch.float16
    tensor = image.half() if half else image
    tensor = tensor.to(device)
    with torch.inference_mode():
        output = _tiled(net, tensor, net_scale, tile, tile_pad)
    output = output.float()
    if pad_h or pad_w:
        output = output[:, :, :-(pad_h * net_scale) if pad_h else None,
                        :-(pad_w * net_scale) if pad_w else None]
    if outscale != net_scale:
        output = F.interpolate(output, scale_factor=outscale / net_scale,
                               mode="bicubic", antialias=True)
    if device == "cuda":
        peak = torch.cuda.max_memory_allocated() / (1024 ** 2)
    else:
        peak = 0.0
    return output.clamp(0, 1), peak
