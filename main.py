"""Main module of amlight/sdntrace_cp Kytos Network Application.

An OpenFlow Path Trace
"""

from kytos.core import KytosNApp, log
from kytos.core.helpers import listen_to
from pyof.foundation.network_types import Ethernet

from napps.amlight.sdntrace import settings
from napps.amlight.sdntrace.shared.switches import Switches
from napps.amlight.sdntrace_cp.tracing.trace_manager import TraceManager



class Main(KytosNApp):
    """Main class of amlight/sdntrace NApp.

    This application gets the list of flows from the switches
    and uses it to trace paths without using the data plane.
    """

    def setup(self):
        """ Default Kytos/Napps setup call. """
        log.info("Starting Kytos SDNTrace App!")

        # Create list of switches
        self.switches = Switches(self.controller.switches)

        # Instantiate TraceManager
        self.tracing = TraceManager(self.controller)

    @rest('/trace', methods=['PUT'])
    def rest_new_trace(self):
        return self.tracing.rest_new_trace(request.get_json())

    @rest('/trace/<trace_id>')
    def rest_get_result(self, trace_id):
        return self.tracing.rest_get_result(trace_id)

    def execute(self):
        """

        """
        pass

    def shutdown(self):
        """

        """
        pass
