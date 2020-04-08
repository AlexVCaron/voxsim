from enum import Enum


class SimulationRunnerException(Exception):
    class ExceptionType(Enum):
        Initialization = 0
        Parameters = 1
        Fiberfox = 2
        Voxsim = 3
        Finalization = 4
        Default = 5

    def __init__(
            self, message, err_type=ExceptionType.Default, err_code=None, streams=None, str_traceback=False
    ):
        self.message = message
        self.err_type = err_type
        self.err_code = err_code
        self.streams = streams
        self.str_tbk = str_traceback

    def get_traceback(self):
        return "[OUT] : {}\n[ERR] : {}\n".format(*self.streams) if self.streams else ""

    def __str__(self):
        err_code = "Error code : {} | ".format(self.err_code) \
            if self.err_code else ""
        traceback = self.get_traceback() if self.str_tbk else ""
        return "{} | {}Simulation runner encountered an error\n{}\n{}".format(
            self.err_type.name, err_code, self.message, traceback
        )
