"""Registered stubs for architectures planned in later phases.

They conform to the ``Pipeline`` interface so the registry, config validation,
CLI, and benchmark runner already know about them — implementing one means
replacing its ``run`` body, not wiring new plumbing.
"""

from __future__ import annotations

from raglab.core.registry import register
from raglab.core.types import RAGResult
from raglab.pipelines.base import BasePipeline

# name -> (roadmap phase, one-line description)
# Phase 2 + Phase 3 architectures are now implemented in their own modules; this
# map is intentionally empty but kept so future planned architectures register
# the same way.
_PLANNED: dict[str, tuple[str, str]] = {}


def _make_stub(arch_name: str, phase: str, desc: str) -> type:
    class _Stub(BasePipeline):
        name = arch_name

        def run(self, query: str) -> RAGResult:
            raise NotImplementedError(
                f"Architecture {arch_name!r} is planned for {phase}: {desc}. "
                f"It is registered against the Pipeline interface but not yet implemented."
            )

    _Stub.__name__ = f"{arch_name}_stub"
    return _Stub


for _name, (_phase, _desc) in _PLANNED.items():
    register("architecture", _name)(_make_stub(_name, _phase, _desc))
