"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""


from sidecar_comms.handlers.main import get_kernel_variables
from sidecar_comms.models import CommMessage


def inbound_comm(comm, open_msg):
    """Handles messages from the sidecar."""

    @comm.on_msg
    def _recv(msg):
        data = msg["content"]["data"]
        # echo for debugging
        comm.send({"status": "received", "data": data})

        # TODO: pydantic discriminators for message types->handlers
        if data.get("msg") == "get_kernel_variables":
            variables = get_kernel_variables()
            msg = CommMessage(
                body=variables,
                handler="get_kernel_variables",
            )
            comm.send(msg.dict())

    comm.send({"status": "connected", "source": "inbound_comm"})
