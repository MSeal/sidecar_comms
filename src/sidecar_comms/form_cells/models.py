from typing import Any, List, Literal

from pydantic import BaseModel


class DatetimePickerModel(BaseModel):
    type: Literal["datetime_picker"] = "datetime_picker"
    value: str
    # TODO: ISO validation?


class DropdownModel(BaseModel):
    type: Literal["dropdown"] = "dropdown"
    value: str
    options: List[Any]


class SliderModel(BaseModel):
    type: Literal["slider"] = "slider"
    value: int = 0
    min: int = 0
    max: int = 10
    step: int = 1


class MultiDropdownModel(BaseModel):
    type: Literal["multi_dropdown"] = "multi_dropdown"
    value: List[str]
    options: List[Any]


class TextInputModel(BaseModel):
    type: Literal["text_input"] = "text_input"
    value: str
    min_length: int = 0
    max_length: int = 1000
