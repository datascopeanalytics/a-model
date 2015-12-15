from .base import Report


class BalanceSheet(Report):
    report_name = 'balance_sheet'
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
        self.load_table()

        # get the dates
        dates = []
        for cell in self.iter_cells_in_row(1, 1):
            dates.append(self.get_date_from_cell(cell))

        # get the values
        for row in self.iter_rows():
            account = row[0].value.strip().replace(' ', '')
            if account == 'TotalBankAccounts':
                for date, cell in zip(dates, row[1:]):
                    self._historical_cash_in_bank.append((date, cell.value))
        return self._historical_cash_in_bank
