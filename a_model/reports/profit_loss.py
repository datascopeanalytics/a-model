import openpyxl

from .base import Report


class ProfitLoss(Report):
    report_name = 'profit_loss.xls'
    gsheet_tab_name = 'P&L'

    def _get_historical_values(self, value_row):
        historical_values = []
        worksheet = self.open_worksheet()

        # exclude the first column (name of accounts) and last column (total)
        min_col = 'B'
        max_col = openpyxl.cell.get_column_letter(
            worksheet.get_highest_column() - 1
        )
        date_cells = self.iter_cells_in_row(5, min_col, max_col)
        value_cells = self.iter_cells_in_row(value_row, min_col, max_col)
        for date_cell, value_cell in zip(date_cells, value_cells):
            historical_values.append((
                self.get_date_from_cell(date_cell),
                self.get_float_from_cell(value_cell),
            ))
        return historical_values

    def get_historical_revenues(self):
        return self._get_historical_values(8)

    def get_historical_costs(self):
        return self._get_historical_values(76)

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/ProfitAndLossReport'),
            ('column', 'monthly'),
        ) + self.get_date_customized_params()

    def _get_ytd_value(self, historical_values):
        now = self.get_now()
        ytd_value = 0.0
        for date, value in reversed(historical_values):
            if now.year > date.year:
                break
            ytd_value += value
        return ytd_value

    def get_ytd_revenue(self):
        historical_revenues = self.get_historical_revenues()
        return self._get_ytd_value(historical_revenues)

    def get_ytd_cost(self):
        historical_costs = self.get_historical_costs()
        return self._get_ytd_value(historical_costs)
