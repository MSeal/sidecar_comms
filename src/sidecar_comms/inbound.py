"""
Comm target registration and message handling for inbound messages.
(Sidecar -> kernel)
"""

from deepmerge import always_merger
from ipykernel.comm import Comm
from IPython import get_ipython

from sidecar_comms.form_cells.base import FORM_CELL_CACHE, parse_as_form_cell
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

        try:
            # deep merge the original form cell with the update data
            update_data = always_merger.merge(form_cell.dict(), data)
            # convert back to one of our FormCell types
            updated_form_cell = parse_as_form_cell(update_data)
            # preserve the observers
            updated_form_cell._observers = form_cell._observers
        except Exception as e:
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())
            return

        FORM_CELL_CACHE[form_cell_id] = updated_form_cell
        get_ipython().user_ns[data["variable_name"]] = updated_form_cell

    if inbound_msg == "create_form_cell":
        # form cell object created from the frontend
        cell_id = data.pop("cell_id")

        try:
            form_cell = parse_as_form_cell(data)
        except Exception as e:
            msg = CommMessage(body={"status": "error", "error": str(e)})
            comm.send(msg.dict())
            return

        get_ipython().user_ns[data["variable_name"]] = form_cell
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
