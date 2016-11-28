from .base import Report
from .exceptions import ReportError


class UnpaidInvoices(Report):
    report_name = 'unpaid_invoices'
    download_method = 'quickbooks'

    def __init__(self, *args, **kwargs):
        super(UnpaidInvoices, self).__init__(*args, **kwargs)
        self._cached_projected_payments = None

    def get_projected_payments(self):
        if self._cached_projected_payments:
            return self._cached_projected_payments
        self._cached_projected_payments = projected_payments = []
        self.load_table()
        min_row = 3
        max_row = self.get_max_cell().row - 2
        date_cells = self.iter_cells_in_col(4, min_row, max_row)
        balance_cells = self.iter_cells_in_col(6, min_row, max_row)
        for date_cell, balance_cell in zip(date_cells, balance_cells):
            if date_cell.value:
                projected_payments.append((
                    self.get_date_from_cell(date_cell),
                    balance_cell.value,
                ))

        # error checking to make sure we're reading the unpaid invoices
        # correctly
        if not projected_payments or sum(zip(*projected_payments)[1]) == 0.0:
            raise ReportError('not reading invoice_projections.csv correctly')

        return projected_payments

    def __iter__(self):
        projected_payments = self.get_projected_payments()
        for date, balance in projected_payments:
            yield date, balance

    def get_qbo_query_params(self):
        return (
            ('rptId', 'txreports/AgingDetailReport'),
            ('token', 'AR_AGING_DET'),
        ) + self.get_report_date_customized_params()
