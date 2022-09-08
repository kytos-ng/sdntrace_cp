"""Module to test the scheduler.py"""
from unittest import TestCase
from kytos.core import log
from napps.amlight.sdntrace_cp.scheduler import Scheduler


class TestScheduler(TestCase):
    """Test class Scheduler"""

    def test_remove_job_fail(self):
        """Test remove_job log with non existent id"""
        scheduler = Scheduler()
        scheduler.remove_job('id')
        self.assertLogs(log, level='info')
