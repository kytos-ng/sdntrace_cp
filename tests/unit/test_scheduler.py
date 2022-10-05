"""Module to test the scheduler.py"""
from unittest import TestCase
from unittest.mock import MagicMock
from napps.amlight.sdntrace_cp.scheduler import Scheduler
from apscheduler.jobstores.base import JobLookupError


class TestScheduler(TestCase):
    """Test class Scheduler"""

    def test_remove_job(self):
        """Test remove_job with existent id"""
        scheduler = Scheduler()
        trigger_args = {'trigger': 'interval', 'seconds': 2}
        scheduler.add_callable('mock_id', MagicMock, **trigger_args)
        self.assertIsNotNone(scheduler.get_job('mock_id'))
        scheduler.remove_job('mock_id')
        self.assertIsNone(scheduler.get_job('mock_id'))

    def test_remove_job_fail(self):
        """Test remove_job with non existent id"""
        scheduler = Scheduler()
        try:
            scheduler.remove_job('mock_id')
        except JobLookupError:
            self.fail("scheduler.remove_job() raised an error")

    def test_get_job(self):
        """Test get_job and add_callable"""
        scheduler = Scheduler()
        trigger_args = {'trigger': 'interval', 'seconds': 2}
        scheduler.add_callable('mock_id', MagicMock, **trigger_args)
        self.assertIsNotNone(scheduler.get_job('mock_id'))
