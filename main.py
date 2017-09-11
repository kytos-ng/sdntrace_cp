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

    This application allows users to trace a path directly from the data
    plane. Originally written for Ryu (github.com/amlight/sdntrace), this app
    is being ported to Kytos.
    Steps:
        1 - User requests a trace using a specific flow characteristic,
            for example VLAN = 1000 Dest TCP Port = 25
        2 - REST module inserts trace request in a queue provided by the
            TraceManager
        3 - The TraceManager runs the Tracer, basically sending PacketOuts
            and waiting for PacketIn till reaching a timeout
        4 - After Timeout, result is provided back to REST that provides it
            back to user
    Dependencies:
        * - of_topology will discovery will the topology
        * - sdntrace_coloring will color all switches

    At this moment, only OpenFlow 1.0 is supported.
    """

    def setup(self):
        """ Default Kytos/Napps setup call. """
        log.info("Starting Kytos SDNTrace App!")

        # Create list of switches
        self.switches = Switches(self.controller.switches)

        # Instantiate TraceManager
        self.tracing = TraceManager(self.controller)

        # Register REST methods
        self.register_rest()

    def register_rest(self):
        """Register REST calls to be used.
        PUT /sdntrace/trace returns a trace_id and
            it is used to request a trace
        GET /sdntrace/trace/<trace_id> is used to collect
            results using the trace_id provided
        """
        endpoints = [('/sdntrace_cp/trace',
                      self.tracing.rest_new_trace_cp,
                      ['PUT']),
                     ('/sdntrace_cp/trace/<trace_id>',
                      self.tracing.rest_get_result_cp,
                      ['GET'])]
        for endpoint in endpoints:
            self.controller.register_rest_endpoint(*endpoint)

    def execute(self):
        """

        """
        pass

    def shutdown(self):
        """

        """
        pass
