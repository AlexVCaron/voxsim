

class AcquisitionProfile:
    def __init__(self, resolution, spacing):
        self._resolution = resolution
        self._spacing = spacing
        self._echo_time = None
        self._repetition = None
        self._n_coils = None
        self._dwell = None
        self._partial = None
        self._scale = None
        self._reverse = False

    def set_echo(self, echo_time):
        self._echo_time = echo_time
        return self

    def get_echo(self):
        return self._echo_time

    def set_repetition(self, repetition_time):
        self._repetition = repetition_time
        return self

    def get_repetition(self):
        return self._repetition

    def set_n_coils(self, n_coils):
        self._n_coils = n_coils
        return self

    def get_n_coils(self):
        return self._n_coils

    def set_dwell(self, dwell_time):
        self._dwell = dwell_time
        return self

    def get_dwell(self):
        return self._dwell

    def set_partial_fourier(self, partial_fourier):
        self._partial = partial_fourier
        return self

    def get_partial_fourier(self):
        return self._partial

    def set_scale(self, scale):
        self._scale = scale
        return self

    def get_scale(self):
        return self._scale

    def set_reverse_phase(self, reverse_phase):
        self._reverse = reverse_phase
        return self

    def get_reverse_phase(self):
        return self._reverse
