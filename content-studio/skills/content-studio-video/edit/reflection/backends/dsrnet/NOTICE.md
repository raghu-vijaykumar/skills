# DSRNet backend provenance

## Code

`model.py` and `lrm.py` are copied from **XReflection**:

- Repository: <https://github.com/hainuo-wang/XReflection>
- Revision: `38512e1e9854a497122142d012fce01bfaa93b4d` (2026-06-04)
- Upstream paths: `xreflection/archs/dsrnet_arch.py`,
  `xreflection/archs/dsrnet/lrm.py`

Only the imports and the `ARCH_REGISTRY` decorator were removed so the network
can run without the XReflection training stack (Lightning, OpenCV, W&B).

### License status

The upstream README states: "This project is licensed under the Apache License
2.0. See the LICENSE file for details." However, the repository contains **no
LICENSE.md or LICENSE file**, and GitHub reports no detected license for the
repository. The Apache-2.0 declaration is therefore recorded here as
**declared but unverified**. Confirm redistribution terms with the upstream
authors before publishing this backend outside a private working copy.

## Weights

- URL: <https://checkpoints.mingjia.li/dsr-25.8915.ckpt>
- Size: 1,657,092,053 bytes
- SHA-256: `337e23a63fd93fc154330a6bbe21894ebd030fe9b8fa68ea7a6c8173e90f83aa`
- Training run: XReflection `train_sirs_dsrnet` (epoch 64, step 128500)

The checkpoint is **not** bundled with this repository. The adapter downloads
it to the per-user content-studio cache on request (`--download`) or reads the
path in `CONTENT_STUDIO_REFLECTION_WEIGHTS`.

The adapter also uses torchvision's `vgg19` ImageNet weights
(`VGG19_Weights.IMAGENET1K_V1`) for the perceptual features that DSRNet expects
as a second input. Torchvision downloads those weights to the standard Torch
cache on first use.

## Paper

DSRNet is described in the XReflection model zoo (NTIRE 2025 single-image
reflection removal challenge). The model predicts a transmission layer, a
reflection layer, and a residual; the adapter relies on the published forward
signature `model(image, vgg_features)`.
