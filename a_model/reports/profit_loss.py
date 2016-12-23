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

    def combine_historical_values_pair(self, result, another_result):
        for i, (date, value) in enumerate(another_result):
            assert result[i][0] == date
            result[i][1] += value
        return result

    def combine_historical_values(self, *row_names):
        result = self.get_historical_values(row_names[0])
        result = map(list, result)
        for row_name in row_names[1:]:
            result = self.combine_historical_values_pair(
                result,
                self.get_historical_values(row_name),
            )
        return result

    def get_historical_revenues(self):
        return self.combine_historical_values(
            'Gross Profit',
            'Total Other Income',
        )

    def get_historical_costs(self):
        return self.combine_historical_values(
            'Total Expenses',
            'Total Other Expenses',
        )

    def get_historical_retirement_costs(self):
        return self.get_historical_values('401(k) Profit Sharing Contribution')

    def get_qbo_query_params(self):
        return (
            ('rptId', 'reports/ProfitAndLossReport'),
            ('column', 'monthly'),
        ) + self.get_date_range_customized_params()

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

    def get_historical_office_costs(self):
        return self.combine_historical_values(
            'Rent Expense',
            'Total Utilities',  # jacked by cloud computing resources
            'Internet',
        )

    def get_historical_fixed_costs(self):
        historical_other_fixed_costs = self.combine_historical_values(
            'Marketing',
            'Public Relations',
            'Bookkeeping',
            'Accounting',
            'Registered Agent',
        )
        historical_office_costs = self.get_historical_office_costs()
        return self.combine_historical_values_pair(
            historical_other_fixed_costs,
            historical_office_costs,
        )

    def get_average_fixed_cost(self):
        historical_fixed_costs = self.get_historical_fixed_costs()
        return sum(historical_fixed_costs) / len(historical_fixed_costs)
