"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""
import traceback
from typing import Optional

from ipykernel.comm import Comm
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from pydantic.utils import deep_update

from sidecar_comms.form_cells.base import FORM_CELL_CACHE, parse_as_form_cell
from sidecar_comms.handlers.main import get_kernel_variables, rename_kernel_variable
from sidecar_comms.models import CommMessage


def inbound_comm(comm, open_msg):
    """Handles messages from the sidecar."""

    @comm.on_msg
    def _recv(msg):
        data = msg["content"]["data"]
        # echo for debugging
        echo_msg = CommMessage(body={"status": "received", "data": data})
        comm.send(echo_msg.dict())

        try:
            handle_msg(data, comm)
        except Exception as e:
            # echo back any errors in the event we can't print/log to an output
            error_msg = CommMessage(
                body={
                    "status": "error",
                    "error": f"error handling message: {e} -> {traceback.format_exc()}",
                    "msg": msg,
                }
            )
            comm.send(error_msg.dict())

    comm.send({"status": "connected", "source": "sidecar_comms"})


def handle_msg(
    data: dict,
    comm: Comm,
    ipython_shell: Optional[InteractiveShell] = None,
) -> None:
    """Checks the message type and calls the appropriate handler."""
    inbound_msg = data.pop("msg", None)

    # TODO: pydantic discriminators for message types->handlers
    if inbound_msg == "get_kernel_variables":
        variables = get_kernel_variables()
        msg = CommMessage(
            body=variables,
            handler="get_kernel_variables",
        )
        comm.send(msg.dict())

    if inbound_msg == "rename_kernel_variable":
        if "old_name" in data and "new_name" in data:
            status = rename_kernel_variable(
                data["old_name"],
                data["new_name"],
                ipython_shell=ipython_shell,
            )
            msg = CommMessage(
                body={"status": status},
                handler="rename_kernel_variable",
            )
            comm.send(msg.dict())

    if inbound_msg == "update_form_cell":
        form_cell_id = data.pop("form_cell_id")
        form_cell = FORM_CELL_CACHE[form_cell_id]
        # deep merge the original form cell with the update data
        update_data = deep_update(form_cell.dict(), data)
        # convert back to one of our FormCell types
        updated_form_cell = parse_as_form_cell(update_data)
        # TODO: migrate the observers from previous form cell to new one
        # updated_form_cell._observers = form_cell._observers
        # send a comm back to the sidecar to update form cell tracking
        msg = CommMessage(
            body=updated_form_cell.dict(),
            handler="update_form_cell",
        )
        comm.send(msg.dict())

        FORM_CELL_CACHE[form_cell_id] = updated_form_cell
        get_ipython().user_ns[data["model_variable_name"]] = updated_form_cell

    if inbound_msg == "create_form_cell":
        # form cell object created from the frontend
        cell_id = data.pop("cell_id")
        form_cell = parse_as_form_cell(data)
        get_ipython().user_ns[data["model_variable_name"]] = form_cell
        # send a comm message back to the sidecar to allow it to track
        # the cell id to form cell id mapping by echoing the provided cell_id
        # and also including the newly-generated form cell model that includes
        # the form cell id (uuid) and any other default properties
        msg = CommMessage(
            body={"cell_id": cell_id, **form_cell.dict()},
            handler="register_form_cell",
        )
        comm.send(msg.dict())

    if inbound_msg == "assign_value_variable":
        form_cell_id = data["form_cell_id"]
        form_cell = FORM_CELL_CACHE[form_cell_id]
        value_variable_name = data["value_variable_name"]
        form_cell._update_value_variable(value_variable_name)
