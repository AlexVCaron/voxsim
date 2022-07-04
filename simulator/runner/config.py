import dataclasses
import pathlib

import simulator.default as default


@dataclasses.dataclass
class SingularityConfig:
    singularity: pathlib.Path = default.SINGULARITY
    singularity_exec: str = default.SINGULARITY_EXEC
