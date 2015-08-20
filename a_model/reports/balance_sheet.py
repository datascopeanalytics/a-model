from .base import Report


class BalanceSheet(Report):
    report_name = 'balance_sheet.xlsx'
    gsheet_tab_name = 'Balance Sheet'

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/BalanceSheetReport'),
            ('token', 'BAL_SHEET'),
            ('column', 'monthly'),
            ('collapse_subs', 'true'),
        ) + self.get_date_customized_params()

    def get_current_cash_in_bank(self):
        worksheet = self.open_worksheet()
        cash_in_bank = 0.0
        for row in worksheet.iter_rows():
            account = row[0].value
            if account and account.strip() == 'Total Bank Accounts':
                formula = row[-1].value
                formula = formula.replace('(', '').replace(')', '')
                for cell in formula.strip('=').split('+'):
                    try:
                        amount = float(worksheet[cell].value.strip('='))
                    except ValueError:
                        amount = 0.0
                    cash_in_bank += amount
        return cash_in_bank
