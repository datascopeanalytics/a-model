from .base import Report


class BalanceSheet(Report):
    report_name = 'balance_sheet'
    gsheet_tab_name = 'Balance Sheet'
    download_method = 'quickbooks'
    upload_method = 'gdrive'

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
        self.load_table()
        self._historical_cash_in_bank = \
            self.get_historical_values('TotalBankAccounts')
        return self._historical_cash_in_bank
