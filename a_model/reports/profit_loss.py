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
        assert len(result) == len(another_result)
        for i, (date, value) in enumerate(another_result):
            assert result[i][0] == date
            result[i][1] += value
        return result

    def combine_historical_values(self, *row_names):
        self.load_table()
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

    def _get_ytd_value(self, historical_values, year=None):
        now = self.get_now()
        ytd_value = 0.0
        year = year or now.year
        for date, value in reversed(historical_values):
            if date.year == year and date.month <= now.month:
                ytd_value += value
        return ytd_value

    def get_ytd_revenue(self, year=None):
        historical_revenues = self.get_historical_revenues()
        return self._get_ytd_value(historical_revenues, year=year)

    def get_ytd_cost(self, year=None):
        historical_costs = self.get_historical_costs()
        return self._get_ytd_value(historical_costs, year=year)

    def get_ytd_margin(self, year=None):
        return self.get_ytd_revenue(year=year) - self.get_ytd_cost(year=year)

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

    def get_historical_personnel_costs(self):
        salary = self.combine_historical_values(
            'Total Payroll Expenses',
            'Total Guaranteed Payments',
        )
        benefits = self.combine_historical_values(
            'Health Insurance',
            '401(k) Profit Sharing Contribution',
            '401(k) Safe Harbor Contribution',
            '401(k) Safe Harbor Contribution - Partners',
        )
        return self.combine_historical_values_pair(salary, benefits)

    def get_average_fixed_cost(self):
        historical_fixed_costs = self.get_historical_fixed_costs()
        return sum(historical_fixed_costs) / len(historical_fixed_costs)
