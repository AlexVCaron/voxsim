from setuptools import setup, find_packages
import glob


if __name__ == "__main__":
    setup(
        name='simulation_generator',
        version='1.0.0',
        packages=find_packages(exclude=("test", "test.*")),
        url='',
        license='',
        author='avcaron',
        author_email='',
        description='',
        data_files=[('.', ["config.py", "config.json"])],
        scripts=list(filter(lambda s: "init" not in s, glob.glob("scripts/*.py")))
    )
