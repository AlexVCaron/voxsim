import typing
import pathlib

SINGULARITY_PATH: typing.Final[pathlib.PurePath] = pathlib.PurePath()
SINGULARITY_NAME: typing.Final[str] = "voxsim_singularity_latest.sif"
SINGULARITY: typing.Final[pathlib.PurePath] = SINGULARITY_PATH / SINGULARITY_NAME
SINGULARITY_EXEC: typing.Final[str] = "singularity"
