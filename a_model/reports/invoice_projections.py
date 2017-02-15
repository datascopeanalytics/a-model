import datetime

from .base import Report


class InvoiceProjections(Report):
    report_name = 'invoice_projections'
    gsheet_tab_name = 'Invoice Projections'
    download_method = 'gdrive'

    def __init__(self, *args, **kwargs):
        super(InvoiceProjections, self).__init__(*args, **kwargs)
        self._cached_invoice_projections = None

    def get_invoice_projections(self):
        if self._cached_invoice_projections:
            return self._cached_invoice_projections
        self._cached_invoice_projections = invoice_projections = []
        self.load_table()

        # aggregate all of the dates
        dates = []
        first_col = 4
        for cell in self.iter_cells_in_row(0, first_col):
            dates.append(self.get_date_from_cell(cell))

        # iterate over all of the projected invoices for all clients
        for row in self.iter_rows(min_row=1):
            for date, cell in zip(dates, row[first_col:]):
                if cell.value:
                    invoice_projections.append((date, cell.value))
        return invoice_projections

    def __iter__(self):
        now = self.get_now()
        for date, amount in self.get_invoice_projections():
            if date <= now:
                raise ValueError((
                    "Double check invoice Projections spreadsheet. There is a "
                    "projected invoice in the past. Try specifying --today"
                ))
            yield date, amount

    def get_total(self, date=None):
        """Get the total expected invoices through `date`. By default, `date`
        is expected to be November of the current fiscal year.
        """
        # if this is the report for november or december, this should be the
        # projections for the next fiscal year
        now = self.get_now()
        date = date or datetime.date(now.year, 11, 30)
        if date <= now:
            date = datetime.date(now.year+1, 11, 30)
        total = 0.0
        for invoice_date, amount in self:
            if invoice_date <= date:
                total += amount
        return total
