import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import Field, PrivateAttr

from sidecar_comms.form_cells.observable import Change, ObservableModel
from sidecar_comms.outbound import comm_manager

FORM_CELL_CACHE: Dict[str, "FormCellBase"] = {}


class FormCellBase(ObservableModel):
    _comm: PrivateAttr
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def __init__(self, **data):
        super().__init__(**data)
        self._comm = comm_manager().open_comm("form_cells")
        FORM_CELL_CACHE[self.id] = self
        self.observe(self._sync_sidecar)

    def __repr__(self):
        props = ", ".join(f"{k}={v}" for k, v in self.dict(exclude=["id"]))
        return f"<{self.__class__.__name__} {props}>"

    def _sync_sidecar(self, change: Change):
        """Send a comm_msg to the sidecar to update the form cell metadata."""
        self._comm.send(handler="update_form_cell", body={"data": change.dict()})

    def _ipython_display_(self):
        """Send a message to the sidecar and print the form cell repr."""
        self._comm.send(handler="display_form_cell", body={"data": self.dict()})
        print(self.__repr__())


# --- Specific models ---
class Datetime(FormCellBase):
    input_type: Literal["datetime"] = "datetime"
    value: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Dropdown(FormCellBase):
    input_type: Literal["dropdown"] = "dropdown"
    value: str = ""
    options: List[Any]


class Slider(FormCellBase):
    input_type: Literal["slider"] = "slider"
    value: int = 0
    min: int = 0
    max: int = 10
    step: int = 1


class Multiselect(FormCellBase):
    input_type: Literal["multiselect"] = "multiselect"
    value: List[str] = Field(default_factory=list)
    options: List[Any]


class Text(FormCellBase):
    input_type: Literal["text"] = "text"
    value: str = ""
    min_length: int = 0
    max_length: int = 1000


FormCell = Annotated[
    Union[
        Datetime,
        Dropdown,
        Slider,
        Multiselect,
        Text,
    ],
    Field(discriminator="input_type"),
]
