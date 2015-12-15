import os
import glob
import importlib
import inspect

from . import base
from ar_aging import ARAging
from balance_sheet import BalanceSheet
from profit_loss import ProfitLoss
from unpaid_invoices import UnpaidInvoices
from revenue_projections import RevenueProjections
from roster import Roster


def _iter_module_names():
    this_filename = os.path.abspath(__file__)
    this_dir = os.path.dirname(this_filename)
    for py_filename in glob.glob(os.path.join(this_dir, '*.py')):
        if py_filename != this_filename:
            filename_root, _ = os.path.splitext(py_filename)
            module_name = os.path.basename(filename_root)
            yield module_name


def _get_report_cls(module_name):
    module = importlib.import_module('.' + module_name, __package__)
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, base.Report):
            return obj
    return None


AVAILABLE_REPORTS = []
for module_name in _iter_module_names():
    report_cls = _get_report_cls(module_name)
    if report_cls and report_cls.report_name:
        AVAILABLE_REPORTS.append(report_cls.report_name)


def cache_quickbooks_locally(username, password, reports=None):
    """Download data from various locations"""
    reports = reports or AVAILABLE_REPORTS

    # these things all come from quickbooks and require selenium
    with base.Browser() as browser:
        browser.login_quickbooks(username, password)
        for report_cls in [ARAging, BalanceSheet, ProfitLoss, UnpaidInvoices]:
            if report_cls.report_name in reports:
                report_cls().download_from_quickbooks(browser)

    # this is manually entered in a google spreadsheet
    for report_cls in [RevenueProjections, Roster]:
        if report_cls.report_name in reports:
            report_cls().download_from_quickbooks(browser)


def sync_local_cache_with_gdrive(reports=None):
    """We only need to upload these reports to Google Drive"""
    reports = reports or AVAILABLE_REPORTS
    for report_cls in [ARAging, BalanceSheet, ProfitLoss]:
        if report_cls.report_name in reports:
            report_cls().upload_to_gdrive()
