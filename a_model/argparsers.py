import argparse
import datetime

from . import reports


# cherry picked from http://stackoverflow.com/a/8527629/564709
class DefaultListAction(argparse.Action):
    CHOICES = list(reports.AVAILABLE_REPORTS)

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            for value in values:
                if value not in self.CHOICES:
                    actions = ', '.join([repr(action)
                                         for action in self.CHOICES])
                    message = ("invalid choice: {0!r} (choose from {1})"
                               .format(value, actions))
                    raise argparse.ArgumentError(self, message)
            setattr(namespace, self.dest, values)


class BaseParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(BaseParser, self).__init__(*args, **kwargs)
        self.add_argument(
            '--today',
            metavar='YYYY-MM-DD',
            type=self.date_type,
            help='run simulations as if today were YYYY-MM-DD',
            default=datetime.date.today()
        )

    def date_type(self, s):
        return datetime.datetime.strptime(s, '%Y-%m-%d').date()


class SyncParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super(SyncParser, self).__init__(*args, **kwargs)
        choices_str = ', '.join(DefaultListAction.CHOICES)
        self.add_argument(
            'reports',
            metavar='REPORT_NAME',
            nargs='*',
            type=str,
            help='specific reports you would like to sync (%s)' % choices_str,
            action=DefaultListAction,
            default=DefaultListAction.CHOICES,
        )


class SimulationNamespace(argparse.Namespace):
    def simulate_monthly_cash_kwargs(self):
        return {
            'n_months': self.n_months,
            'n_universes': self.n_universes,
            'verbose': self.verbose,
            'ontime_payment': self.ontime_payment,
            'ontime_completion': self.ontime_completion,
        }


class SimulationParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super(SimulationParser, self).__init__(*args, **kwargs)
        self.add_argument(
            '--n-months',
            metavar='M',
            type=int,
            help='the number of months to simulate (default to end of year)',
            # default=self._n_months_to_end_of_year(),
            default=12,
        )
        self.add_argument(
            '--n-universes',
            metavar='U',
            type=int,
            help='the number of universes to simulate',
            default=1000,
        )
        self.add_argument(
            '--ontime-payment',
            action="store_true",
            help='remove noise in payments',
        )
        self.add_argument(
            '--ontime-completion',
            action="store_true",
            help='remove project completion noise',
        )
        self.add_argument(
            '--ontime',
            action="store_true",
            help='equivalent to --ontime-payment --ontime-completion',
        )
        self.add_argument(
            '-v', '--verbose',
            action="store_true",
            help='print more information during the simulations',
        )

    def parse_args(self):
        namespace = super(SimulationParser, self).parse_args(
            namespace=SimulationNamespace()
        )
        if namespace.ontime:
            namespace.ontime_completion = namespace.ontime
            namespace.ontime_payment = namespace.ontime
        return namespace


class HiringParser(SimulationParser):

    def __init__(self, *args, **kwargs):
        super(HiringParser, self).__init__(*args, **kwargs)
        self.add_argument(
            '--n-n00bs',
            metavar='N',
            type=int,
            help='the number of new people to consider adding to Datascope',
            default=3,
        )


class CalculateBonusParser(BaseParser):

    def __init__(self, *args, **kwargs):
        super(CalculateBonusParser, self).__init__(*args, **kwargs)
        self.add_argument(
            '-p', '--prepare-csv',
            action='store_true',
            help='prepare the CSV to be used in creating the bonuses',
        )
        self.add_argument(
            '-i', '--input-csv',
            default='bonus.csv',
            help='the input spreadsheet to use for the bonus calculation',
        )
