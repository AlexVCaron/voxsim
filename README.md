# Simulation Generator

Project setup
=============

The whole project's library can be installed via with the help of **setuptools**.
The project requires **Python 3** to run in order for all the functionalities to
work, on a **Linux** based operating system.

Prerequisites
-------------

- Singularity **3** or **greater**
- MPI libraries
  - On Ubuntu, install `openmpi-bin`
- A good multi-core CPU
- RAM sized to the number of fibers simulated
  - ~90ko per fiber at 100 interpolation samples

Installation
------------

- Create a **virtualenv** on a Python 3.7 interpreter and activate it

- Install required packages with
  
  `pip install -r requirements.txt`

- Install the project inside the virtual environment with 

  `python setup.py install`
