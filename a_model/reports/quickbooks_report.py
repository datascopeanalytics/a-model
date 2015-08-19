import os
import datetime

import openpyxl

from .. import utils


class QuickbooksReport(object):
    report_name = None

    def __init__(self):
        self.filename = os.path.join(
            utils.DATA_ROOT, self.report_name
        )

    def open_worksheet(self):
        # all of the quickbooks reports only have one active sheet
        workbook = openpyxl.load_workbook(self.filename)
        self.worksheet = workbook.active
        return self.worksheet

    def _row_cell_range(self, row, min_col, max_col):
        return '%(min_col)s%(row)d:%(max_col)s%(row)d' % locals()

    def _col_cell_range(self, col, min_row, max_row):
        return '%(col)s%(min_row)d:%(col)s%(max_row)d' % locals()

    def _iter_cells_in_range(self, cell_range):
        for row in self.worksheet.iter_rows(cell_range):
            for cell in row:
                yield cell

    def iter_cells_in_row(self, row, min_col, max_col):
        cell_range = self._row_cell_range(row, min_col, max_col)
        return self._iter_cells_in_range(cell_range)

    def iter_cells_in_column(self, col, min_row, max_row):
        cell_range = self._col_cell_range(col, min_row, max_row)
        return self._iter_cells_in_range(cell_range)

    def get_date_from_cell(self, date_cell):
        try:
            date = datetime.datetime.strptime(date_cell.value, '%b %Y')
        except ValueError:
            date = utils.qbo_date(date_cell.value)
        return utils.end_of_month(date)

    def get_float_from_cell(self, float_cell):
        if float_cell.value is None:
            return 0.0
        elif isinstance(float_cell.value, (float, int)):
            return float(float_cell.value)
        else:
            return float(float_cell.value.strip('='))
