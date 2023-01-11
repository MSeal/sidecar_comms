from typing import Callable, Union

from pydantic import parse_obj_as
from traitlets import HasTraits, Int, Unicode

from sidecar_comms.form_cells import models
from sidecar_comms.outbound import comm_manager

FormCellModel = Union[
    models.DatetimePickerModel,
    models.DropdownModel,
    models.SliderModel,
    models.MultiDropdownModel,
    models.TextInputModel,
]


class FormCell:
    def __init__(self, type: str, **kwargs):
        self._type = type
        self._parent_model = parse_obj_as(FormCellModel, {"type": self._type, **kwargs})
        self._parent_traitlet = self._setup_traitlet()
        self._comm = self._setup_comm()

    def __repr__(self):
        cell_name = self._parent_model.__class__.__name__.replace("Model", "")
        props = ", ".join(f"{k}={v}" for k, v in self._parent_model.dict().items() if k != "type")
        return f"<{cell_name} {props}>"

    def _setup_comm(self):
        return comm_manager().open_comm("form_cells")

    def _setup_traitlet(self):
        traitlet = HasTraits()

        traits_to_add = {}
        for name, d in self._parent_model.schema()["properties"].items():
            if name == "type":
                continue
            if d["type"] == "string":
                traits_to_add[name] = Unicode()
            elif d["type"] == "integer":
                traits_to_add[name] = Int()

        traitlet.add_traits(**traits_to_add)
        traitlet.observe(self._sync_sidecar, type="change")
        return traitlet

    def observe(self, fn: Callable, **kwargs):
        self._parent_traitlet.observe(fn, **kwargs)

    @property
    def value(self):
        return self._parent_model.value

    @value.setter
    def value(self, value):
        self._parent_model.value = value
        self._parent_traitlet.value = value

    def _sync_sidecar(self, change: dict):
        """Send a comm_msg to the sidecar to update the form cell metadata."""
        # remove 'owner' since comms can't serialize traitlet objects
        data = {k: v for k, v in change.items() if k != "owner"}
        data["id"] = id(self)
        self._comm.send(handler="update_form_cell", body={"data": data})

    def _ipython_display_(self):
        """Send a message to the sidecar and print the form cell repr."""
        data = self._parent_model.dict()
        data["id"] = id(self)
        self._comm.send(handler="display_form_cell", body={"data": data})
        print(self.__repr__())


# --- Specific models ---


class DatetimePicker(FormCell):
    def __init__(self, **kwargs):
        super().__init__(type="datetime_picker", **kwargs)


class Dropdown(FormCell):
    def __init__(self, **kwargs):
        super().__init__(type="dropdown", **kwargs)

    @property
    def options(self):
        return self._parent_model.options

    @options.setter
    def options(self, value):
        self._parent_model.options = value


class IntSlider(FormCell):
    def __init__(self, **kwargs):
        super().__init__(type="slider", **kwargs)


class MultiDropdown(Dropdown):
    def __init__(self, **kwargs):
        super().__init__(type="multi_dropdown", **kwargs)


class TextInput(FormCell):
    def __init__(self, **kwargs):
        super().__init__(type="text_input", **kwargs)
