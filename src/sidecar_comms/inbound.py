"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""


from sidecar_comms.form_cells.base import FORM_CELL_CACHE
from sidecar_comms.handlers.main import get_kernel_variables


def inbound_comm(comm, open_msg):
    """Handles messages from the sidecar."""

    @comm.on_msg
    def _recv(msg):
        data = msg["content"]["data"]
        # echo for debugging
        comm.send({"status": "received", "data": data})

        # TODO: pydantic discriminators for message types->handlers
        if data.get("msg") == "get_kernel_variables":
            msg = get_kernel_variables()
            comm.send(msg)

        if data.get("msg") == "update_form_cell_value":
            comm.send({"status": "updating form cell value"})
            form_cell_id = data["form_cell_id"]
            form_cell = FORM_CELL_CACHE[form_cell_id]
            value = data["value"]
            # TODO: handle when non-`value` attributes change
            comm.send({"status": f"updating {form_cell_id} -> {str(form_cell)} with {value=}"})
            form_cell.value = value

    comm.send({"status": "connected", "source": "sidecar_comms"})
