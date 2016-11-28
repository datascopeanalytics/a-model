class RowNotFound(Exception):
    def __init__(self, row_name):
        self.row_name = row_name

    def __str__(self):
        return (
            'could not find a row named "%(row_name)s"'
        ) % vars(self)


class ColNotFound(Exception):
    def __init__(self, col_name):
        self.col_name = col_name

    def __str__(self):
        return (
            'could not find a col named "%(col_name)s"'
        ) % vars(self)


class ReportError(Exception):
    pass
