from .base import Report
from .. import utils


class ARAging(Report):
    report_name = 'ar_aging'
    gsheet_tab_name = 'A/R Aging'
    download_method = 'quickbooks'
    upload_method = 'gdrive'

    def get_qbo_query_params(self):
        return (
            ('rptId', 'AR_AGING'),
        ) + self.get_report_date_customized_params()
