"""
Comm opening and message formatting for outbound messages.
(Kernel -> sidecar -> kernel)
"""
from sidecar_comms.manager import get_comm_manager
from sidecar_comms.models import BaseWidget


# some sample functions to send a quick message via new comm to the sidecar
def get_cell_ids():
    comm_manager = get_comm_manager()
    comm = comm_manager.open_comm("cell_ids")
    comm.send(body={"request": "get_cell_ids"})
    widget = BaseWidget()
    widget.comm = comm
    return widget


def get_kernel_status():
    comm_manager = get_comm_manager()
    comm = comm_manager.open_comm("kernel_status")
    comm.send(body={"request": "get_kernel_status"})
    widget = BaseWidget()
    widget.comm = comm
    return widget
