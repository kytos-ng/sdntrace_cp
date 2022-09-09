"""scheduler used by the sndtrace_cp

This module is intended to replace the usage of the napp
called scheduler soon to be deprecated.
"""
import pytz
from apscheduler.schedulers.background import BackgroundScheduler


class Scheduler:
    """Class to set scheduler."""

    def __init__(self) -> None:
        """Create an instance of Scheduler and starts it."""
        self.scheduler = BackgroundScheduler(timezone=pytz.utc)
        self.scheduler.start()

    # pylint: disable=too-many-arguments
    def add_callable(self, id_, func, trigger, args=None, kwargs=None,
                     **trigger_args):
        """Add job to scheduler"""
        self.scheduler.add_job(func, trigger=trigger, args=args, kwargs=kwargs,
                               id=id_, **trigger_args)

    def remove_job(self, id_):
        """Remove job from scheduler"""
        self.scheduler.remove_job(id_)

    def shutdown(self, wait):
        """Shut down scheduler.
        Delete the jobs inside the scheduler before calling
        this function.
        """
        self.scheduler.shutdown(wait)

    def get_job(self, id_):
        """Return an scheduled job with id_ as id"""
        return self.scheduler.get_job(id_)
