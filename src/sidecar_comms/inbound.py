"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""

from ipykernel.comm import Comm
from IPython import get_ipython
from pydantic import ValidationError, parse_obj_as

from sidecar_comms.form_cells.base import FORM_CELL_CACHE, FormCell, valid_model_input_types
from sidecar_comms.handlers.main import get_kernel_variables
from sidecar_comms.models import CommMessage


def inbound_comm(comm, open_msg):
    """Handles messages from the sidecar."""

    @comm.on_msg
    def _recv(msg):
        data = msg["content"]["data"]
        # echo for debugging
        msg = CommMessage(body={"status": "received", "data": data})
        comm.send(msg.dict())

        try:
            handle_msg(data, comm)
        except Exception as e:
            # echo back any errors in the event we can't print/log to an output
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())

    comm.send({"status": "connected", "source": "sidecar_comms"})


def handle_msg(data: dict, comm: Comm) -> None:
    """Checks the message type and calls the appropriate handler."""
    inbound_msg = data.pop("msg", None)

    # TODO: pydantic discriminators for message types->handlers
    if inbound_msg == "get_kernel_variables":
        variables = get_kernel_variables()
        msg = CommMessage(body=variables, handler="get_kernel_variables")
        comm.send(msg.dict())

    if inbound_msg == "update_form_cell":
        form_cell_id = data.pop("form_cell_id")
        form_cell = FORM_CELL_CACHE[form_cell_id]
        # potentially update more than just `value`
        try:
            updated_form_cell = form_cell.copy(update=data)
            FORM_CELL_CACHE[form_cell_id] = updated_form_cell
            get_ipython().user_ns[data["variable_name"]] = updated_form_cell
            msg = CommMessage(body={"status": f"updated {updated_form_cell=}"})
            comm.send(msg.dict())
        except Exception as e:
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())
            return

    if inbound_msg == "create_form_cell":
        # form cell object created from the frontend
        form_cell_data = data.copy()
        cell_id = form_cell_data.pop("cell_id")

        # check if the input_type is valid before parsing into a model
        # in case we need to overwrite it as "custom"
        if form_cell_data["input_type"] not in valid_model_input_types:
            form_cell_data["input_type"] = "custom"

        try:
            form_cell = parse_obj_as(FormCell, form_cell_data)
        except ValidationError as e:
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())
            return

        get_ipython().user_ns[form_cell_data["variable_name"]] = form_cell
        # send a comm message back to the sidecar to allow it to track
        # the cell id to form cell id mapping by echoing the provided cell_id
        # and also including the newly-generated form cell model that includes
        # the form cell id (uuid) and any other default properties
        msg = CommMessage(
            body={"cell_id": cell_id, **form_cell.dict()},
            handler="register_form_cell",
        )
        comm.send(msg.dict())

    if inbound_msg == "delete_form_cell":
        try:
            variable_name = data["variable_name"]
            form_cell = get_ipython().user_ns.get(variable_name)
            if form_cell is not None:
                del get_ipython().user_ns[variable_name]
                msg = CommMessage(
                    body={"cell_id": data["cell_id"], **form_cell.dict()},
                    handler="deregister_form_cell",
                )
                comm.send(msg.dict())
        except Exception as e:
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())
            return
