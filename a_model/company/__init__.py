from .company import BaseCompany
from .goals import GoalCompanyMixin
from .forecasts import ForecastCompanyMixin


class Company(BaseCompany, GoalCompany, ForecastCompany):
    """Use this Company object throughout. Splitting things into a BaseCompany,
    GoalCompany and ForecastCompany is purely for code organizational purposes.
    """
    pass
