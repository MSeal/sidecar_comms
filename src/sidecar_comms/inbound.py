"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""

from IPython import get_ipython
from pydantic import ValidationError, parse_obj_as

from sidecar_comms.form_cells.base import FORM_CELL_CACHE, FormCell, create_custom_form_cell
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

        if data.get("msg") == "update_form_cell":
            form_cell_id = data["form_cell_id"]
            form_cell = FORM_CELL_CACHE[form_cell_id]
            value = data["value"]
            # TODO: handle when non-`value` attributes change
            # form_cell._receiving_update = True
            form_cell.value = value
            # form_cell._receiving_update = False

        if data.get("msg") == "create_form_cell":
            # form cell object created from the frontend
            form_cell_data = data.copy()
            _ = form_cell_data.pop("msg")
            cell_id = form_cell_data.pop("cell_id")

            try:
                form_cell = parse_obj_as(FormCell, form_cell_data)
            except ValidationError as e:
                if "No match for discriminator" not in str(e):
                    comm.send({"status": "error", "error": str(e)})
                    return
                custom_model = create_custom_form_cell(form_cell_data)
                form_cell = parse_obj_as(custom_model, form_cell_data)

            get_ipython().user_ns[form_cell_data["input_variable"]] = form_cell
            # send a comm message back to the sidecar to allow it to track
            # the cell id to form cell id mapping by echoing the provided cell_id
            # and also including the newly-generated form cell model that includes
            # the form cell id (uuid) and any other default properties
            msg = CommMessage(
                body={"cell_id": cell_id, **form_cell.dict()},
                handler="register_form_cell",
            )
            comm.send(msg.dict())

    comm.send({"status": "connected", "source": "sidecar_comms"})
