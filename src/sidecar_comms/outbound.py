"""
Comm opening and message formatting for outbound messages.
(Kernel -> sidecar)
"""
from functools import lru_cache
from typing import Optional

from ipykernel.comm import Comm
from traitlets import Any, HasTraits

from sidecar_comms.models import CommMessage


class SidecarComm(Comm, HasTraits):
    value = Any().tag(sync=True)

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

    def update_value(self, msg):
        data = msg["content"]["data"]
        self.value = data.get("value")


class CommManager:
    comms = {}

    def open_comm(
        self,
        target_name: str,
        data: Optional[dict] = None,
    ) -> SidecarComm:
        """
        Creates a SidecarComm and sends a message to the sidecar for registration.
        This will allow values to be sent back here to the comm
        and be accessed via comm.value.
        """
        if target_name in self.comms:
            return self.comms[target_name]

        comm = SidecarComm(target_name=target_name, data=data)
        self.comms[target_name] = comm

        msg = CommMessage(
            body={"target": target_name},
            handler="register_comm_target",
        )
        comm.send(msg.dict())

        # if a message with {"value": X} is sent to this comm,
        # update the comm's value attribute
        comm.on_msg(comm.update_value)

        return comm


@lru_cache
def comm_manager() -> CommManager:
    return CommManager()
