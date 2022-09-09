"""Module to test the scheduler.py"""
from unittest import TestCase
from unittest.mock import MagicMock
from apscheduler.jobstores.base import JobLookupError
from napps.amlight.sdntrace_cp.scheduler import Scheduler


class TestScheduler(TestCase):
    """Test class Scheduler"""

    def test_remove_job_fail(self):
        """Test remove_job log with non existent id"""
        scheduler = Scheduler()
        with self.assertRaises(JobLookupError):
            scheduler.remove_job('id')

    def test_get_job(self):
        """Test get_job and add_callable"""
        scheduler = Scheduler()
        trigger_args = {'trigger': 'interval', 'seconds': 2}
        scheduler.add_callable('mock_id', MagicMock, **trigger_args)
        self.assertIsNotNone(scheduler.get_job('mock_id'))
