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
        self, message, err_type=ExceptionType.Default, err_code=None, log=None
    ):
        self.message = message
        self.err_type = err_type
        self.err_code = err_code
        self.log = log

    def __str__(self):
        err_code = (
            "Error code : {} | ".format(self.err_code) if self.err_code else ""
        )
        log_link = (
            "Inspect log for more informations :\n   - {}".format(self.log)
            if self.log
            else ""
        )
        return "{} | {}Simulation runner encountered an error\n{}\n{}".format(
            self.err_type.name, err_code, self.message, log_link
        )
