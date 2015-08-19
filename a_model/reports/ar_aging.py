from .base import Report
from .. import utils

class ARAging(Report):
    report_name = 'ar_aging.xlsx'
    gsheet_tab_name = 'A/R Aging'

    def get_qbo_query_params(self):
        return (
            ('rptId', 'AR_AGING'),
            ('report_date', utils.qbo_date_str(self.end_date)),
            ('date_macro', 'custom'),
            ('customized', 'yes'),
        )
