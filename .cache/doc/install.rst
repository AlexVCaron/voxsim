Project setup
=============

The whole project's library can be installed via with the help of **setuptools**. The project
requires **Python 3** to run in order for all the functionalities to work, on a **Linux** based
operating system.

Prerequisites
-------------

- singularity **3** or **greater**
- a good multi-core CPU
- RAM sized to the number of fibers simulated (approx 90ko per fiber at 100 samples)

Installation
------------

- Create a **virtualenv** on a Python 3.7 interpreter and activate it

- Run the appropriate requirements file, either if you have access to the internet or not (in
  which case you must use *requirements_cluster.txt**)

   pip install -r requirements.txt

- Install the project inside the virtual environment

   python setup.py install
