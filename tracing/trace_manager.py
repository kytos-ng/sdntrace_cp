"""
    Trace Manager Class
"""
import dill
import time
import json
from flask import request, jsonify
from _thread import start_new_thread as new_thread

from kytos.core import log
from napps.amlight.sdntrace import settings, constants
from napps.amlight.sdntrace.shared.switches import Switches
from napps.amlight.sdntrace_cp.tracing.tracer import TracePath
from napps.amlight.sdntrace.tracing.trace_manager \
    import TraceManager as DPTraceManager


class TraceManager(DPTraceManager):
    """
        The TraceManager class is the class responsible to
        manage all trace requests.
    """

    @staticmethod
    def is_entry_valid(entries):
        """ Make sure the switch selected by the user exists and
        that it has a color using the Coloring Napp.
        In fact, this method has to validate all params provided.

        Args:
            entries: dictionary with user request
        Returns:
            True: all set
            False: switch requested doesn't exist
        """
        dpid = entries['trace']['switch']['dpid']
        init_switch = Switches().get_switch(dpid)
        if isinstance(init_switch, bool):
            return False
        return True
