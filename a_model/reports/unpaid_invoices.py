from .base import Report


class UnpaidInvoices(Report):
    report_name = 'unpaid_invoices.csv'

    def __init__(self, *args, **kwargs):
        super(UnpaidInvoices, self).__init__()
        self._cached_projected_payments = None

    def get_projected_payments(self):
        if self._cached_projected_payments:
            return self._cached_projected_payments
        self._cached_projected_payments = projected_payments = []
        worksheet = self.open_worksheet()

        min_row = 6
        max_row = worksheet.max_row - 4
        date_cells = self.iter_cells_in_column('G', min_row, max_row)
        balance_cells = self.iter_cells_in_column('I', min_row, max_row)
        for date_cell, balance_cell in zip(date_cells, balance_cells):
            projected_payments.append((
                self.get_date_from_cell(date_cell),
                self.get_float_from_cell(balance_cell),
            ))
        return projected_payments

    def __iter__(self):
        projected_payments = self.get_projected_payments()
        for date, balance in projected_payments:
            yield date, balance

    def get_qbo_query_params(self):
        return (
            ('rptId', 'txreports/TxListReport'),
            ('arpaid', '2'),
            ('token', 'INVOICE_LIST'),
        ) + self.get_date_customized_params()
