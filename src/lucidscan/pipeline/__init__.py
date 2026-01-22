"""Pipeline orchestration for lucidshark.

Manages the execution of scan pipeline stages:
1. Scanner execution (parallel by default)
2. Enricher execution (sequential, in configured order)
3. Result aggregation (metadata and summary)
"""

from lucidshark.pipeline.executor import PipelineConfig, PipelineExecutor
from lucidshark.pipeline.parallel import ParallelScannerExecutor, ScannerResult

__all__ = [
    "PipelineConfig",
    "PipelineExecutor",
    "ParallelScannerExecutor",
    "ScannerResult",
]
