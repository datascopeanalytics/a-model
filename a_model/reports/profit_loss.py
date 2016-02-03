from .base import Report


class ProfitLoss(Report):
    report_name = 'profit_loss'
    gsheet_tab_name = 'P&L'
    download_method = 'quickbooks'
    upload_method = 'gdrive'

    def _get_historical_values(self, row):
        historical_values = []
        self.load_table()

        # exclude the first column (name of accounts) and last column (total)
        min_col = 1
        max_col = self.get_max_cell().col - 1
        date_cells = self.iter_cells_in_row(1, min_col, max_col)
        value_cells = self.iter_cells_in_row(row, min_col, max_col)
        for date_cell, value_cell in zip(date_cells, value_cells):
            historical_values.append((
                self.get_date_from_cell(date_cell),
                value_cell.value or 0.0,
            ))
        return historical_values

    def get_historical_revenues(self):
        return self._get_historical_values(6)

    def get_historical_costs(self):
        return self._get_historical_values(72)

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/ProfitAndLossReport'),
            ('column', 'monthly'),
        ) + self.get_date_customized_params()

    def _get_ytd_value(self, historical_values):
        now = self.get_now()
        ytd_value = 0.0
        for date, value in reversed(historical_values):
            if now.year > date.year:
                break
            ytd_value += value
        return ytd_value

    def get_ytd_revenue(self):
        historical_revenues = self.get_historical_revenues()
        return self._get_ytd_value(historical_revenues)

    def get_ytd_cost(self):
        historical_costs = self.get_historical_costs()
        return self._get_ytd_value(historical_costs)

    def get_average_fixed_cost(self):
        fixed_cost_accounts = set([
            'Marketing',
            'PublicRelations',
            'Bookkeeping',
            'Accounting',
            'RegisteredAgent',
            'RentExpense',
            'TotalUtilities',
        ])
        historical_fixed_costs = []
        for cell in self.iter_cells_in_col(0):
            if cell.value in fixed_cost_accounts:
                historical_account = self._get_historical_values(cell.row)
                if not historical_fixed_costs:
                    historical_fixed_costs = [0.0] * len(historical_account)
                for i in range(len(historical_account)):
                    historical_fixed_costs[i] += historical_account[i][1]
        return sum(historical_fixed_costs) / len(historical_fixed_costs)

    def get_historical_per_person_costs(self):
        fixed_cost = self.get_average_fixed_cost()
        historical_per_person_costs = []
        for _, cost in self.get_historical_costs():
            # TODO: improve this when we correctly account for start and end
            # dates for people. this is tentatively a really bad way to address
            # this.
            per_person_cost = (cost - fixed_cost) / 9.0
            historical_per_person_costs.append(per_person_cost)
        return historical_per_person_costs
