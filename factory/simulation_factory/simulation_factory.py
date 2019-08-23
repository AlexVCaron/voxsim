from factory.simulation_factory.parameters.acquisition_profile import AcquisitionProfile
from factory.simulation_factory.parameters.artifact_model import ArtifactModel
from factory.simulation_factory.parameters.gradient_profile import StejskalTannerType, GradientProfile
from .simulation_handler import SimulationHandler


class SimulationFactory:

    @staticmethod
    def get_simulation_handler(geometry_handler):
        return SimulationHandler(
            geometry_handler.get_resolution(),
            geometry_handler.get_spacing(),
            geometry_handler.get_compartments()
        )

    @staticmethod
    def generate_acquisition_profile(
            echo_time,
            repetition_time,
            n_channels,
            dwell_time=1,
            partial_fourier=1,
            signal_scale=100,
            reverse_phase=False
    ):
        return AcquisitionProfile(None, None).set_echo(echo_time)\
                                             .set_repetition(repetition_time)\
                                             .set_n_coils(n_channels)\
                                             .set_dwell(dwell_time)\
                                             .set_partial_fourier(partial_fourier)\
                                             .set_scale(signal_scale)\
                                             .set_reverse_phase(reverse_phase)

    @staticmethod
    def generate_gradient_profile(bvals, bvecs, g_type=StejskalTannerType()):
        return GradientProfile(bvals, bvecs, g_type)

    @staticmethod
    def generate_artifact_model(*artifact_models):
        return ArtifactModel(artifact_models)

    @staticmethod
    def generate_noise_model(noise_type, variance):
        return {"descr": "noise", "type": noise_type, "var": variance}

    @staticmethod
    def generate_motion_model(randomize=False, direction_indexes="random", rotation=(0, 0, 0), translation=(0, 0, 0)):
        return {
            "descr": "motion",
            "random": randomize,
            "directions": direction_indexes,
            "rot": rotation,
            "trans": translation
        }

    @staticmethod
    def generate_eddy_current_model(gradient_strength):
        return {"descr": "eddy", "gradient": gradient_strength}

    @staticmethod
    def generate_ghosting_model(k_space_offset):
        return {"descr": "ghost", "offset": k_space_offset}

    @staticmethod
    def generate_signal_spikes_model(number_of_spikes, scale):
        return {"descr": "spikes", "number": number_of_spikes, "scale": scale}

    @staticmethod
    def generate_aliasing_model(fov_shrink_percent):
        return {"descr": "aliasing", "fov": fov_shrink_percent}

    @staticmethod
    def generate_stick_compartment(diffusivity, t1, t2, number):
        return {
            "type": "fiber",
            "model": "stick",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": number
        }

    @staticmethod
    def generate_tensor_compartment(d1, d2, d3, t1, t2, number, c_type="fiber"):
        return {
            "type": c_type,
            "model": "tensor",
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "t1": t1,
            "t2": t2,
            "ID": number
        }

    @staticmethod
    def generate_ball_compartment(diffusivity, t1, t2, number):
        return {
            "type": "non-fiber",
            "model": "ball",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": number
        }