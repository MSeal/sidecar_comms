"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""

from IPython import get_ipython
from pydantic import parse_obj_as

from sidecar_comms.form_cells.base import FORM_CELL_CACHE, FormCell
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
            form_cell_id = data["form_cell_id"]
            form_cell = FORM_CELL_CACHE[form_cell_id]
            value = data["value"]
            # TODO: handle when non-`value` attributes change
            # form_cell._receiving_update = True
            form_cell.value = value
            # form_cell._receiving_update = False

        if data.get("msg") == "create_form_cell":
            form_cell_data = data.copy()
            form_cell_data.pop("msg")
            form_cell = parse_obj_as(FormCell, form_cell_data)
            get_ipython().user_ns[form_cell_data["input_variable"]] = form_cell

    comm.send({"status": "connected", "source": "sidecar_comms"})
