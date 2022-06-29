import dataclasses

import simulator.default as default


@dataclasses.dataclass
class SingularityConfig:
    singularity_path: str = default.SINGULARITY_PATH
    singularity_name: str = default.SINGULARITY_NAME
    singularity_exec: str = default.SINGULARITY_EXEC
