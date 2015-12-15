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


def _is_child_class(child_cls, parent_cls):
    return child_cls != parent_cls and issubclass(child_cls, parent_cls)


def _get_report_cls(module_name):
    module = importlib.import_module('.' + module_name, __package__)
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and _is_child_class(obj, base.Report):
            return obj
    return None

# automatically detect which reports need to be downloaded form quickbooks,
# gdrive, and uploaded back to gdrive depending on class attributes on the
# report objects
AVAILABLE_REPORTS = set()
DOWNLOAD_QUICKBOOKS_REPORTS = set()
DOWNLOAD_GDRIVE_REPORTS = set()
UPLOAD_GDRIVE_REPORTS = set()
for module_name in _iter_module_names():
    report_cls = _get_report_cls(module_name)
    if report_cls and report_cls.report_name:
        AVAILABLE_REPORTS.add(report_cls.report_name)
        if report_cls.download_method == 'quickbooks':
            DOWNLOAD_QUICKBOOKS_REPORTS.add(report_cls)
        elif report_cls.download_method == 'gdrive':
            DOWNLOAD_GDRIVE_REPORTS.add(report_cls)
        elif report_cls.download_method is not None:
            raise ValueError((
                'download_method must be either "quickbooks", "gdrive", '
                'or None'
            ))
        if report_cls.upload_method == 'gdrive':
            UPLOAD_GDRIVE_REPORTS.add(report_cls)
        elif report_cls.upload_method is not None:
            raise ValueError(
                'upload_method must be either "gdrive" or None'
            )


def cache_quickbooks_locally(username, password, reports=None):
    """Download data from various locations"""
    reports = reports or AVAILABLE_REPORTS

    # determine which quickbooks reports need to be downloaded before
    # instantiating a browser instance
    download_quickbooks_reports = []
    for report_cls in DOWNLOAD_QUICKBOOKS_REPORTS:
        if report_cls.report_name in reports:
            download_quickbooks_reports.append(report_cls)

    # these things all come from quickbooks and require selenium
    if download_quickbooks_reports:
        with base.Browser() as browser:
            browser.login_quickbooks(username, password)
            for report_cls in download_quickbooks_reports:
                report_cls().download_from_quickbooks(browser)

    # this is manually entered in a google spreadsheet
    for report_cls in DOWNLOAD_GDRIVE_REPORTS:
        if report_cls.report_name in reports:
            report_cls().download_from_gdrive()


def sync_local_cache_with_gdrive(reports=None):
    """We only need to upload these reports to Google Drive"""
    reports = reports or AVAILABLE_REPORTS
    for report_cls in UPLOAD_GDRIVE_REPORTS:
        if report_cls.report_name in reports:
            report_cls().upload_to_gdrive()
