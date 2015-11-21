from .base import Report


class RevenueProjections(Report):
    report_name = 'revenue_projections.csv'
    gsheet_tab_name = 'Revenue Projections'

    def __init__(self, *args, **kwargs):
        super(RevenueProjections, self).__init__()
        self._cached_revenue_projections = None

    def get_revenue_projections(self):
        if self._cached_revenue_projections:
            return self._cached_revenue_projections
        self._cached_revenue_projections = revenue_projections = []
        self.load_table()

        # aggregate all of the dates
        dates = []
        first_col = 2
        for cell in self.iter_cells_in_row(0, first_col):
            dates.append(self.get_date_from_cell(cell))

        # iterate over all of the projected revenues for all clients
        for row in self.iter_rows(min_row=1):
            for date, cell in zip(dates, row[first_col:]):
                if cell.value:
                    revenue_projections.append((date, cell.value))
        return revenue_projections

    def __iter__(self):
        now = self.get_now()
        for date, amount in self.get_revenue_projections():
            if date < now:
                raise ValueError((
                    "Double check Revenue Projections spreadsheet. There is a "
                    "projected revenue in the past"
                ))
            yield date, amount
