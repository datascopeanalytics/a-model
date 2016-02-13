from .base import Report


class ProfitLoss(Report):
    report_name = 'profit_loss'
    gsheet_tab_name = 'P&L'
    download_method = 'quickbooks'
    upload_method = 'gdrive'

    def get_historical_values(self, row_name):
        return super(ProfitLoss, self).get_historical_values(
            row_name,
            max_col=self.get_max_cell().col-1,
        )

    def get_historical_revenues(self):
        return self.get_historical_values('Gross Profit')

    def get_historical_costs(self):
        return self.get_historical_values('Total Expenses')

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

    def get_historical_fixed_costs(self):
        fixed_cost_accounts = [
            'Marketing',
            'Public Relations',
            'Bookkeeping',
            'Accounting',
            'Registered Agent',
            'Rent Expense',
            'Total Utilities',
        ]
        historical_fixed_costs = []
        for fixed_cost_account in fixed_cost_accounts:
            historical_account = self.get_historical_values(fixed_cost_account)
            if not historical_fixed_costs:
                historical_fixed_costs = [0.0] * len(historical_account)
            for i in range(len(historical_account)):
                historical_fixed_costs[i] += historical_account[i][1]
        return historical_fixed_costs

    def get_average_fixed_cost(self):
        historical_fixed_costs = self.get_historical_fixed_costs()
        return sum(historical_fixed_costs) / len(historical_fixed_costs)
