# Simulation Generator

Project setup
=============

The whole project's library can be installed via with the help of **setuptools**.
The project requires **Python 3** to run in order for all the functionalities to
work, on a **Linux** based operating system.

Prerequisites
-------------

- Singularity **3** or **greater**
  - The singularity image for voXSim can be pulled with `singularity pull library://avcaron/default/voxsim_singularity`
- MPI libraries
  - On Ubuntu, install `openmpi-bin`
- A good multi-core CPU
- RAM sized to the number of fibers simulated
  - ~90ko per fiber at 100 interpolation samples

Documentation
-------------

The project is partially documented; the documentation is generated using sphinx, as well as the 
autodoc module. To build the documentation, run the `build_documentation.sh` script at the base 
of the project.

Installation
------------

- Create a python **virtual environment** (virtualenv, pyenv, etc.) and activate it

- Install required packages with
  
  `pip install -r requirements.txt`

- Install the project inside the virtual environment with 

  `python setup.py install`

- To install the project as developper, use

  `pip install -e .` or `python setup.py develop`
