"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""
from IPython import get_ipython

from sidecar_comms.models import CommMessage


def inbound_comm(comm, open_msg):
    @comm.on_msg
    def _recv(msg):
        data = msg["content"]["data"]

        # TODO: pydantic discriminators for message types->handlers
        if data.get("msg") == "get_kernel_variables":
            msg = CommMessage(
                body={"data": dict(get_ipython().user_ns)},
                comm_id=comm.id,
            )
            comm.send(msg.dict())

    # registration acknowledgement
    msg = CommMessage(
        body={"data": "comm registered"},
        comm_id=comm.id,
    )
    comm.send(msg.dict())
