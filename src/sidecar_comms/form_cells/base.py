"""
Form Cells are our "better" version of widgets. On the frontend, they look like widgets but
live in the cell input as opposed to being a cell output. When a cell is switched to "form",
a cell metadata delta is pushed to the sidecar and sidecar sends the info on to the kernel
over Comm.

These models here represent different types of frontend form cells. A Datetime object in
this file represents a date time picker form cell widget on the frontend. 

The backend form cell objects have their state updated when frontend changes (user slides
a slider or fills out a text input) through the same delta to sidecar -> sidecar comm to kernel
flow as when a cell is first switched to "form".

A user can programmatically create a form cell, such as typing model = Datetime() and outputting
model in a cell. In that case, instead of ipython repr'ing the model, we get into the ipython
display override and send a comm message to the sidecar to change the cell to "form".

A user can also programmatically update the state of a form cell, and thanks to the ObservableModel
pattern, those changes will be sent over Comm to the sidecar which will create cell metadata deltas
that update the frontend state.

Finally, the backend implementation of form cells use a discriminator pattern. You can create a
form cell from a dictionary that is coming in from the frontend. Example:

model = pydantic.parse_obj_as(FormCell, {"input_type": "datetime", "value": "2021-01-01"})
model
>>> Datetime(value=datetime.datetime(2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Union

from pydantic import Field, PrivateAttr
from typing_extensions import Annotated

from sidecar_comms.form_cells.observable import Change, ObservableModel
from sidecar_comms.outbound import SidecarComm, comm_manager

FORM_CELL_CACHE: Dict[str, "FormCellBase"] = {}


class FormCellBase(ObservableModel):
    """
    Base class for form cells.
     - registers the class instance in the FORM_CELL_CACHE
     - makes sure comm is open between sidecar and kernel
     - when repr'd, override the ipython display handler and instead send a comm message so
       that the sidecar will create a cell metadata delta that switches the cell type
    """

    _comm: SidecarComm = PrivateAttr()
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


# FormCell is just a type, you can't instantiate FormCell()
# See top of file / module docstring for example usage with pydantic.parse_obj_as
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
