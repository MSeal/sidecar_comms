from typing import Any, Literal

from ipywidgets import Widget, register
from pydantic import BaseModel, Field
from traitlets import Unicode


class CommMessage(BaseModel):
    source: Literal["sidecar_comms"] = "sidecar_comms"
    body: dict[str, Any] = Field(default_factory=dict)
    comm_id: str
    target_name: str


@register
class BaseWidget(Widget):
    _view_name = Unicode("SidecarComms").tag(sync=True)
    _view_module = Unicode("sidecar_comms").tag(sync=True)
    _view_module_version = Unicode("0.1.0").tag(sync=True)

    @property
    def value(self):
        return self.comm.value
