Concepts
========

Modeling MRI Signal
-------------------

There is many approach that can be taken to simulate the magnetization signal obtain from
the water molecules of the brain tissues. Model-free methods are great in that they contain
as little assumptions about the studied tissues as possible. However, they are hare to
parametrize and their parameters are often incomprehensible for the human mind except as
when taken as a whole.

For example, the spherical harmonics are great at modeling an orientation dependant
signal. However, not much can be said of the coefficients of the harmonic, its parameters,
even less how they come together to form exactly the signal emitted by a particular medium.
In order to make some sense of it, some processing must be done to extract relevant metrics
which are interpretable and whose dimensions make some physical sense.

This is henceforth a bad way to take to parametrize the simulator, and to overcome that there
is the model-based methods. They focus at describing the different tissues by their
characteristics and design mathematical relations between those and the MRI signal. Using such
techniques, the simulator can then be parametrized by interpretable and known characteristics.
