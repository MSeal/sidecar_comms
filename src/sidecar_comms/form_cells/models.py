from typing import Any, List, Literal

from pydantic import BaseModel


class DatetimePickerModel(BaseModel):
    input_type: Literal["datetime"] = "datetime"
    value: str
    # TODO: ISO validation?


class DropdownModel(BaseModel):
    input_type: Literal["dropdown"] = "dropdown"
    value: str
    options: List[Any]


class SliderModel(BaseModel):
    input_type: Literal["slider"] = "slider"
    value: int = 0
    min: int = 0
    max: int = 10
    step: int = 1


class MultiDropdownModel(BaseModel):
    input_type: Literal["multiselect"] = "multiselect"
    value: List[str]
    options: List[Any]


class TextInputModel(BaseModel):
    input_type: Literal["text"] = "text"
    value: str
    min_length: int = 0
    max_length: int = 1000
