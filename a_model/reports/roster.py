import datetime

from .base import Report
from .. import utils
from ..person import Person


class Roster(Report):
    report_name = 'roster'
    gsheet_tab_name = 'Roster'
    download_method = 'gdrive'

    def iter_people(self):
        self.load_table()
        for row in self.iter_rows(min_row=1):
            values = [cell.value for cell in row]
            values[1] = cast_as_date(values[1])
            values[2] = cast_as_date(values[2])
            values[3] = cast_as_float(values[3])
            values[4] = cast_as_bool(values[4])
            values[5] = cast_as_date(values[5])
            values[6] = cast_as_float(values[6])
            values = values[:7]
            yield Person(None, *values)


def cast_as_date(date_or_str):
    if isinstance(date_or_str, (str, unicode)):
        try:
            return utils.qbo_date(date_or_str)
        except:
            return None
    elif isinstance(date_or_str, datetime.date):
        return date_or_str
    else:
        raise TypeError('unknown type to cast as date')


def cast_as_float(float_or_str):
    if isinstance(float_or_str, (str, unicode)):
        if float_or_str.endswith('%'):
            float_or_str = float(float_or_str.replace('%', '')) / 100.0
        float_or_str = float_or_str or 0.0
        return float(float_or_str)
    elif isinstance(float_or_str, (float, int, long)):
        return float(float_or_str)
    else:
        raise TypeError('unknown type to cast as float')


def cast_as_bool(value):
    if isinstance(value, (float, int, long)):
        return bool(value)
    else:
        raise TypeError('unknown type to cast as bool')
