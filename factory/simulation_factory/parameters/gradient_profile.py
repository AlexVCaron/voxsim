class StejskalTannerType:
    pass


class TensorValuedByTensorType:
    def __init__(self, tensor):
        self._tensor = tensor

    def get_bval(self):
        return self._tensor[0, 0] + self._tensor[1, 1] + self._tensor[2, 2]


class TensorValuedByEigs:
    def __init__(self, eigenvals):
        self._eigenvals = eigenvals

    def get_bval(self):
        return sum(self._eigenvals)


class TensorValuedByParams:
    def __init__(self, b_iso, b_delta):
        self._b_iso = b_iso
        self._b_delta = b_delta

    def get_bval(self):
        return self._b_iso


class GradientProfile:
    def __init__(self, bvals, bvecs, g_type):
        self._nominal_bval = max(bvals) if type(g_type) is StejskalTannerType else g_type.get_bval()
        self._directions = self._scale_gradients(bvecs, bvals, self._nominal_bval)

    def _scale_gradients(self, bvecs, bvals, nominal_bval):
        pass
