import enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SidecarRequestType(enum.Enum):
    cell_ids = "cell_ids"
    cell_states = "cell_states"
    kernel_state = "kernel_state"


class CommMessageBody(BaseModel):
    request: Optional[SidecarRequestType]
    data: Optional[dict[str, Any]]

    class Config:
        use_enum_values = True


class CommMessage(BaseModel):
    source: Literal["sidecar_comms"] = "sidecar_comms"
    body: CommMessageBody = Field(default_factory=CommMessageBody)
    comm_id: Optional[str] = None
    target_name: Optional[str] = None
