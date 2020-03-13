from setuptools import setup
import glob

if __name__ == "__main__":
    setup(
        name='simulation_generator',
        version='1.0.0',
        packages=['test', 'test.helpers', 'scripts', 'external', 'external.qspace_sampler', 'external.qspace_sampler.visu',
                  'external.qspace_sampler.bases', 'external.qspace_sampler.bases.tests',
                  'external.qspace_sampler.sampling', 'simulator', 'simulator.runner', 'simulator.runner.impl',
                  'simulator.factory', 'simulator.factory.common', 'simulator.factory.geometry_factory',
                  'simulator.factory.geometry_factory.utils', 'simulator.factory.geometry_factory.features',
                  'simulator.factory.geometry_factory.features.ORM',
                  'simulator.factory.geometry_factory.features.ORM.Objects', 'simulator.factory.geometry_factory.handlers',
                  'simulator.factory.simulation_factory', 'simulator.factory.simulation_factory.helpers',
                  'simulator.factory.simulation_factory.handlers', 'simulator.factory.simulation_factory.parameters'],
        url='',
        license='',
        author='avcaron',
        author_email='',
        description='',
        data_files=[('.', ["config.py", "config.json"])],
        scripts=list(filter(lambda s: "init" not in s, glob.glob("scripts/*.py")))
    )
