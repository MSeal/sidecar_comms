from IPython.core.interactiveshell import InteractiveShell

from sidecar_comms.form_cells.base import (
    Checkboxes,
    Custom,
    Datetime,
    Dropdown,
    Slider,
    Text,
    parse_as_form_cell,
)


class TestParseFormCell:
    def test_parse_checkboxes(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "checkboxes",
            "model_variable_name": "test",
            "value": ["test"],
            "variable_type": "str",
            "settings": {
                "options": ["test"],
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "checkboxes"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == ["test"]
        assert form_cell.variable_type == "str"
        assert form_cell.settings.options == ["test"]
        assert isinstance(form_cell, Checkboxes)

    def test_parse_datetime(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "datetime",
            "model_variable_name": "test",
            "value": "2023-01-01T00:00:00Z",
            "variable_type": "datetime",
            "settings": {},
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "datetime"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == "2023-01-01T00:00:00+00:00"
        assert form_cell.variable_type == "datetime"
        assert form_cell.settings == {}
        assert isinstance(form_cell, Datetime)

    def test_parse_dropdown(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "dropdown",
            "model_variable_name": "test",
            "value": ["a"],
            "variable_type": "str",
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "dropdown"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == ["a"]
        assert form_cell.variable_type == "str"
        assert form_cell.settings.options == ["a", "b", "c"]
        assert isinstance(form_cell, Dropdown)

    def test_parse_slider(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "slider",
            "model_variable_name": "test",
            "value": 0,
            "variable_type": "int",
            "settings": {
                "min": 0,
                "max": 100,
                "step": 1,
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "slider"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == 0
        assert form_cell.variable_type == "int"
        assert form_cell.settings.min == 0
        assert form_cell.settings.max == 100
        assert form_cell.settings.step == 1
        assert isinstance(form_cell, Slider)

    def test_parse_text(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "text",
            "model_variable_name": "test",
            "value": "test",
            "settings": {
                "min_length": 0,
                "max_length": 1000,
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "text"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == "test"
        assert form_cell.settings.min_length == 0
        assert form_cell.settings.max_length == 1000
        assert isinstance(form_cell, Text)

    def test_parse_custom(self, get_ipython: InteractiveShell):
        data = {
            "input_type": "my_new_form_cell_type",
            "model_variable_name": "test",
            "value": "test",
            "settings": {"min_foo": 0, "max_bar": 50},
            "form_type": "new_plugin",
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "custom"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == "test"
        assert form_cell.settings.min_foo == 0
        assert form_cell.settings.max_bar == 50
        assert form_cell.form_type == "new_plugin"
        assert isinstance(form_cell, Custom)
