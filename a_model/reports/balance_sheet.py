import openpyxl

from .base import Report


class BalanceSheet(Report):
    report_name = 'balance_sheet.xlsx'
    gsheet_tab_name = 'Balance Sheet'

    def __init__(self, *args, **kwargs):
        super(BalanceSheet, self).__init__(*args, **kwargs)
        self._historical_cash_in_bank = None

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/BalanceSheetReport'),
            ('token', 'BAL_SHEET'),
            ('column', 'monthly'),
            ('collapse_subs', 'true'),
        ) + self.get_date_customized_params()

    def get_current_cash_in_bank(self):
        historical_cash_in_bank = self.get_historical_cash_in_bank()
        return historical_cash_in_bank[-1][1]

    def get_historical_cash_in_bank(self):
        if self._historical_cash_in_bank is not None:
            return self._historical_cash_in_bank
        self._historical_cash_in_bank = []
        worksheet = self.open_worksheet()

        # get the dates
        dates = []
        max_col = openpyxl.cell.get_column_letter(
            worksheet.get_highest_column()
        )
        for cell in self.iter_cells_in_row(5, 'B', max_col):
            dates.append(self.get_date_from_cell(cell))

        # get the values
        for row in worksheet.iter_rows():
            account = row[0].value
            if account and account.strip() == 'Total Bank Accounts':
                for date, cell in zip(dates, row[1:]):
                    self._historical_cash_in_bank.append((
                        date,
                        self._get_cash_in_bank(cell)
                    ))
        return self._historical_cash_in_bank

    def _get_cash_in_bank(self, cell):
        """
        `Total Bank Accounts` cell is actually a sum of all individual bank
        account amounts. Need to do sum by hand.
        """

        formula = cell.value
        formula = formula.replace('(', '').replace(')', '')
        cash_in_bank = 0.0
        for cell in formula.strip('=').split('+'):
            try:
                amount = float(self.worksheet[cell].value.strip('='))
            except:
                amount = 0.0
            cash_in_bank += amount
        return cash_in_bank
