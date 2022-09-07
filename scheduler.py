"""scheduler used by the sndtrace_cp

This module is intended to replace the usage of the napp
called scheduler soon to be deprecated.
"""
import pytz
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from kytos.core import log


class Scheduler:
    """Class to set scheduler."""

    def __init__(self) -> None:
        """Create an instance of Scheduler and starts it."""
        self.scheduler = BackgroundScheduler(timezone=pytz.utc)
        self.scheduler.start()

    def add_job(self, settings):
        """Add job to scheduler"""
        log.info('add_job called')
        func = settings['func']
        job_id = settings['id']
        self.scheduler.add_job(func, id=job_id, **settings['kwargs'])

    def remove_job(self, settings):
        """Remove job from scheduler"""
        log.info('remove_job called')
        job_id = settings['id']
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            log.info(f'Job to start {job_id} already removed/does not exist')

    def shutdown(self, wait):
        """Shut down scheduler.
        Delete the jobs inside the scheduler before calling
        this function.
        """
        self.scheduler.shutdown(wait)
