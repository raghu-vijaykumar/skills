"""DSRNet inference backend.

The architecture in ``model.py`` and ``lrm.py`` is vendored from XReflection
(https://github.com/hainuo-wang/XReflection) at commit
``38512e1e9854a497122142d012fce01bfaa93b4d``. The upstream README declares
Apache-2.0 but the repository has no LICENSE file; see ``NOTICE.md`` for the
exact provenance and license caveat.

Checkpoints are not bundled. ``infer.py`` downloads the released weights on
request and records their SHA-256 in the evidence report.

Imports are lazy so ``dsrnet.geometry`` can be used without torch.
"""

__all__ = ["DSRNet"]


def __getattr__(name):
    if name == "DSRNet":
        from .model import DSRNet
        return DSRNet
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
