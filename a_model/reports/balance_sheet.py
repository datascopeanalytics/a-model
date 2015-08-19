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
