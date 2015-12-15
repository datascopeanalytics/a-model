import argparse
import datetime

from . import reports


class SyncParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(SyncParser, self).__init__(*args, **kwargs)
        self.add_argument(
            'reports',
            metavar='REPORT_NAME',
            nargs='*',
            type=str,
            help='specific reports you would like to sync',
            choices=reports.AVAILABLE_REPORTS,
            default=[],
        )


class SimulationParser(argparse.ArgumentParser):

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
            '-v', '--verbose',
            action="store_true",
            help='print more information during the simulations',
        )


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
