import glob
from setuptools import find_packages, setup

from simulator.utils.setup.documentation import DocCommand

if __name__ == "__main__":
    setup(
        name="simulation_generator",
        version="1.0.1",
        packages=find_packages(exclude=("tests", "tests.*")),
        url="",
        license="",
        author="avcaron",
        author_email="",
        description="",
        scripts=list(
            filter(lambda s: "init" not in s, glob.glob("scripts/*.py"))
        ),
        cmdclass={"documentation": DocCommand},
    )
