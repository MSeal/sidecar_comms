"""
Comm opening and message formatting for outbound messages.
(Kernel -> sidecar)
"""
from functools import lru_cache
from typing import Optional

from ipykernel.comm import Comm

from sidecar_comms.models import BaseWidget, CommMessage


class SidecarComm(Comm):
    value = None

    def send(
        self,
        comm_id: Optional[str] = None,
        target_name: Optional[str] = None,
        **data,
    ) -> None:
        comm_id = comm_id or self.comm_id
        target_name = target_name or self.target_name
        msg = CommMessage(
            comm_id=comm_id,
            target_name=target_name,
            **data,
        )
        super().send(data=msg.dict())

    def _recv(self, msg):
        data = msg["content"]["data"]
        self.value = data.get("value")

    def on_msg(self, func):
        # similar to @comm.on_msg callback registration
        super().on_msg(self._recv)


class CommManager:
    comms = {}

    def open_comm(self, target_name: str, data: Optional[dict] = None) -> None:
        """
        Creates a SidecarComm and sends a message to the sidecar for registration.
        This will allow values to be sent back here to the comm
        and be accessed via comm.value.
        """
        comm = SidecarComm(target_name=target_name, data=data)
        self.comms[target_name] = comm
        comm.send(body={"request": target_name})
        # TODO: figure out why comm.value doesn't update without this
        widget = BaseWidget()
        widget.comm = comm
        return widget


@lru_cache
def comm_manager() -> CommManager:
    return CommManager()
