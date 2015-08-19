import openpyxl

from .base import Report


class ProfitLoss(Report):
    report_name = 'profit_loss.xlsx'
    gsheet_tab_name = 'P&L'

    def get_historical_revenues(self):
        historical_revenues = []
        worksheet = self.open_worksheet()

        # exclude the first column (name of accounts) and last column (total)
        min_col = 'B'
        max_col = openpyxl.cell.get_column_letter(
            worksheet.get_highest_column() - 1
        )
        date_cells = self.iter_cells_in_row(5, min_col, max_col)
        income_cells = self.iter_cells_in_row(8, min_col, max_col)
        for date_cell, income_cell in zip(date_cells, income_cells):
            historical_revenues.append((
                self.get_date_from_cell(date_cell),
                self.get_float_from_cell(income_cell),
            ))
        return historical_revenues

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/ProfitAndLossReport'),
            ('column', 'monthly'),
        ) + self.get_date_customized_params()
