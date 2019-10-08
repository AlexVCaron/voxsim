from enum import Enum

from .parameters import AcquisitionProfile,\
                        ArtifactModel,\
                        GradientProfile,\
                        StejskalTannerType,\
                        TensorValuedByTensorType, \
                        TensorValuedByParamsType,\
                        TensorValuedByEigsType
from .handlers import SimulationHandler
from .qspace_sampler.sampling import multishell


class SimulationFactory:

    class CompartmentType(Enum):
        INTRA_AXONAL = "1"
        INTER_AXONAL = "2"
        EXTRA_AXONAL_1 = "3"
        EXTRA_AXONAL_2 = "4"

    class AcquisitionType(Enum):
        STEJSKAL_TANNER = StejskalTannerType
        TENSOR_VALUED_BY_TENSOR = TensorValuedByTensorType
        TENSOR_VALUED_BY_EIGS = TensorValuedByEigsType
        TENSOR_VALUED_BY_PARAMS = TensorValuedByParamsType

    class NoiseType(Enum):
        COMPLEX_GAUSSIAN = "gaussian"
        RICIAN = "rician"

    @staticmethod
    def get_simulation_handler(geometry_handler, compartments=None):
        return SimulationHandler(
            geometry_handler.get_resolution(),
            geometry_handler.get_spacing(),
            compartments
        )

    @staticmethod
    def generate_acquisition_profile(
            echo_time,
            repetition_time,
            n_channels,
            dwell_time=1,
            partial_fourier=1,
            signal_scale=100,
            reverse_phase=False,
            inhomogen_time=50,
            axon_radius=0
    ):
        return AcquisitionProfile(None, None).set_echo(echo_time)\
                                             .set_repetition(repetition_time)\
                                             .set_n_coils(n_channels)\
                                             .set_dwell(dwell_time)\
                                             .set_partial_fourier(partial_fourier)\
                                             .set_scale(signal_scale)\
                                             .set_reverse_phase(reverse_phase)\
                                             .set_inhomogen_time(inhomogen_time)\
                                             .set_axon_radius(axon_radius)

    @staticmethod
    def generate_gradient_vectors(points_per_shell, max_iter=1000):
        weights = multishell.compute_weights(
            len(points_per_shell),
            points_per_shell,
            [[i for i in range(len(points_per_shell))]],
            [1]
        )
        return multishell.optimize(len(points_per_shell), points_per_shell, weights, max_iter).tolist()

    @staticmethod
    def generate_gradient_profile(
            bvals,
            bvecs,
            n_b0=0,
            g_type=AcquisitionType.STEJSKAL_TANNER,
            *g_type_args,
            **g_type_kwargs
    ):
        return GradientProfile(
            [0 for i in range(n_b0)] + bvals,
            [[0, 0, 0] for i in range(n_b0)] + bvecs,
            g_type.value(*g_type_args, **g_type_kwargs)
        )

    @staticmethod
    def generate_artifact_model(*artifact_models):
        return ArtifactModel(artifact_models)

    @staticmethod
    def generate_noise_model(noise_type, variance):
        return {"descr": "addnoise", "noisetype": noise_type, "noisevariance": variance, "value": True}

    @staticmethod
    def generate_motion_model(randomize=False, direction_indexes="random", rotation=(0, 0, 0), translation=(0, 0, 0)):
        return {
            "descr": "doAddMotion",
            "randomMotion": randomize,
            "motionvolumes": direction_indexes,
            "rotation0": rotation[0],
            "rotation1": rotation[1],
            "rotation2": rotation[2],
            "translation0": translation[0],
            "translation1": translation[1],
            "translation2": translation[2],
            "value": True
        }

    @staticmethod
    def generate_distortion_model():
        return {"descr": "doAddDistortions", "value": True}

    @staticmethod
    def generate_eddy_current_model(gradient_strength, gradient_tau):
        return {"descr": "addeddycurrents", "eddyStrength": gradient_strength, "eddyTau": gradient_tau, "value": True}

    @staticmethod
    def generate_ghosting_model(k_space_offset):
        return {"descr": "addghosts", "kspaceLineOffset": k_space_offset, "value": True}

    @staticmethod
    def generate_signal_spikes_model(number_of_spikes, scale):
        return {"descr": "addspikes", "spikesnum": number_of_spikes, "spikesscale": scale, "value": True}

    @staticmethod
    def generate_aliasing_model(fov_shrink_percent):
        return {"descr": "addaliasing", "aliasingfactor": fov_shrink_percent, "value": True}

    @staticmethod
    def generate_gibbs_ringing_model():
        return {"descr": "addringing", "value": True}

    @staticmethod
    def generate_fiber_stick_compartment(diffusivity, t1, t2, compartment_type):
        assert compartment_type in [
            SimulationFactory.CompartmentType.INTRA_AXONAL, SimulationFactory.CompartmentType.INTER_AXONAL
        ]
        return {
            "type": "fiber",
            "model": "stick",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }

    @staticmethod
    def generate_fiber_tensor_compartment(d1, d2, d3, t1, t2, compartment_type):
        assert compartment_type in [
            SimulationFactory.CompartmentType.INTRA_AXONAL, SimulationFactory.CompartmentType.INTER_AXONAL
        ]
        return {
            "type": "fiber",
            "model": "tensor",
            "d1": d1,
            "d2": d2,
            "d3": d3,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }

    @staticmethod
    def generate_extra_ball_compartment(diffusivity, t1, t2, compartment_type):
        assert compartment_type in [
            SimulationFactory.CompartmentType.EXTRA_AXONAL_1, SimulationFactory.CompartmentType.EXTRA_AXONAL_2
        ]
        return {
            "type": "non-fiber",
            "model": "ball",
            "d": diffusivity,
            "t1": t1,
            "t2": t2,
            "ID": compartment_type.value
        }