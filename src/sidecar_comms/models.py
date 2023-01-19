import enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SidecarRequestType(enum.Enum):
    cell_ids = "cell_ids"
    cell_states = "cell_states"
    form_cells = "form_cells"
    kernel_state = "kernel_state"


class CommMessage(BaseModel):
    source: Literal["sidecar_comms"] = "sidecar_comms"
    body: dict = Field(default_factory=dict)
    comm_id: Optional[str] = None
    target_name: Optional[str] = None
    handler: Optional[str]
