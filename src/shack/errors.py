
class ShackError(Exception): pass


class AlreadyDoneWarning(Warning):

    """This warning is for cases where a directory with results was already
    produced (for example with an evaluation run). The directory is added to
    the warning so that the procedure that intercepts this warning can access
    the directory."""

    def __init__(self, message, results_directory: str):
        super().__init__(message)
        self.results_directory = results_directory
