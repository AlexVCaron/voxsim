from factory.simulation_factory.parameters.acquisition_profile import AcquisitionProfile
from factory.simulation_factory.parameters.artifact_model import ArtifactModel
from factory.simulation_factory.parameters.gradient_profile import GradientProfile


class SimulationHandler:
    def __init__(self, resolution, spacing, compartments):
        self._acq_profile = AcquisitionProfile(resolution, spacing)
        self._art_model = ArtifactModel()
        self._grad_profile = GradientProfile()
        self._compartments = compartments

    def set_compartments(self, compartments):
        self._compartments = compartments
        return self

    def set_acquisition_profile(self, acquisition_profile):
        self._acq_profile.set_echo(acquisition_profile.get_echo())\
                         .set_repetition(acquisition_profile.get_repetition())\
                         .set_n_coils(acquisition_profile.get_n_coils())\
                         .set_dwell(acquisition_profile.get_dwell())\
                         .set_partial_fourier(acquisition_profile.get_partial_fourier())\
                         .set_scale(acquisition_profile.get_scale())\
                         .set_reverse_phase(acquisition_profile.get_reverse_phase())
        return self

    def set_gradient_profile(self, gradient_profile):
        self._grad_profile = gradient_profile

    def set_artifact_model(self, artifact_model):
        self._art_model = artifact_model
