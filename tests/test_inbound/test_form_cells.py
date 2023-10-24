from datetime import datetime, timezone
from unittest.mock import Mock

from ipykernel.comm import Comm

from sidecar_comms.form_cells.base import (
    Checkboxes,
    Custom,
    Datetime,
    Dropdown,
    Slider,
    Text,
    parse_as_form_cell,
)
from sidecar_comms.form_cells.observable import Change, ObservableModel
from sidecar_comms.inbound import handle_msg
from sidecar_comms.shell import get_ipython_shell


class TestParseFormCell:
    def test_parse_checkboxes(self):
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

    def test_parse_datetime(self):
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
        assert form_cell.value == datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
        assert form_cell.variable_type == "datetime"
        assert form_cell.settings == ObservableModel()
        assert isinstance(form_cell, Datetime)

    def test_parse_dropdown(self):
        data = {
            "input_type": "dropdown",
            "model_variable_name": "test",
            "value": "a",
            "variable_type": "str",
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "dropdown"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == "a"
        assert form_cell.variable_type == "str"
        assert form_cell.settings.options == ["a", "b", "c"]
        assert isinstance(form_cell, Dropdown)

    def test_parse_slider(self):
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

    def test_parse_text(self):
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

    def test_parse_custom(self):
        data = {
            "input_type": "my_new_form_cell_type",
            "model_variable_name": "test",
            "value": "test",
            "foo": "bar",
            "settings": {
                "abc": "def",
            },
        }
        form_cell = parse_as_form_cell(data)
        assert form_cell.input_type == "custom"
        assert form_cell.model_variable_name == "test"
        assert form_cell.value == "test"
        assert form_cell.foo == "bar"
        assert form_cell.settings.abc == "def"
        assert isinstance(form_cell, Custom)


class TestFormCellSetup:
    def test_value_variable_created(self):
        """Test that a value variable is created and available in the
        user namespace when a form cell is created."""
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
        assert form_cell.value_variable_name == "test_value"
        assert "test_value" in get_ipython_shell().user_ns


class TestFormCellUpdates:
    def test_value_variable_updated(self):
        """Test that a value variable is updated when the form cell value
        is updated."""
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
        form_cell.value = "new value"
        assert get_ipython_shell().user_ns["test_value"] == "new value"

    def test_update_dict_settings(self):
        """Test that updating a form cell with a nested dictionary
        updates the settings without dropping existing settings
        or altering the original model structure."""
        data = {
            "input_type": "checkboxes",
            "model_variable_name": "test",
            "value": ["a"],
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        update_dict = {"settings": {"options": ["a", "b", "x", "y"]}}
        form_cell.update(update_dict)
        assert form_cell.value == ["a"]
        assert form_cell.settings.options == ["a", "b", "x", "y"]

    def test_update_dict_value_settings(self):
        """Test that updating a form cell with a nested dictionary
        updates the settings without dropping existing settings
        or altering the original model structure."""
        data = {
            "input_type": "checkboxes",
            "model_variable_name": "test",
            "value": ["a"],
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        update_dict = {
            "settings": {"options": ["a", "b", "x", "y"]},
            "value": ["b", "x"],
        }
        form_cell.update(update_dict)
        assert form_cell.value == ["b", "x"]
        assert form_cell.settings.options == ["a", "b", "x", "y"]

    def test_datetime_value_update_format(self):
        """Make sure the value variable doesn't convert to a string datetime during value updates,
        and that it stays a datetime object with tzinfo just like the model value.
        """
        data = {
            "input_type": "datetime",
            "model_variable_name": "test",
            "value": "2023-01-01T00:00:00",
            "settings": {},
        }
        form_cell = parse_as_form_cell(data)
        update_dict = {"value": "2023-03-03T00:00:00"}
        form_cell.update(update_dict)
        assert form_cell.value == datetime(2023, 3, 3, 0, 0, tzinfo=timezone.utc)
        value_variable = get_ipython_shell().user_ns["test_value"]
        assert value_variable == datetime(2023, 3, 3, 0, 0, tzinfo=timezone.utc)


class TestFormCellObservers:
    def test_callback_triggered_on_value_change(self):
        """Test that a callback is triggered when the form cell value
        is updated."""
        data = {
            "input_type": "checkboxes",
            "model_variable_name": "test",
            "value": ["a"],
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        mock_callback = Mock()
        form_cell.observe(mock_callback)
        form_cell.value = ["b"]
        mock_callback.assert_called_once_with(Change(name="value", old=["a"], new=["b"]))

    def test_callback_triggered_on_settings_change(self):
        """Test that a callback is triggered when the form cell settings
        are updated."""
        data = {
            "input_type": "checkboxes",
            "model_variable_name": "test",
            "value": ["a"],
            "settings": {
                "options": ["a", "b", "c"],
            },
        }
        form_cell = parse_as_form_cell(data)
        mock_callback = Mock()
        form_cell.settings.observe(mock_callback)
        form_cell.settings.options = ["a", "b", "x", "y"]
        mock_callback.assert_called_once_with(
            Change(
                name="options",
                old=["a", "b", "c"],
                new=["a", "b", "x", "y"],
            )
        )


class TestCommHandler:
    def test_update_form_cell(self, sample_comm: Comm):
        """
        Test that a update_form_cell comm message is handled properly by pulling the correct form
        cell instance and updating the properties, to include updating the associated
        value variable.

        If an extra property is passed, we should still successfully update the form cell model.
        """
        model_name = "form1_model"
        value_name = "form1"
        form_cell = Slider(value_variable_name=value_name, settings={})
        shell = get_ipython_shell()
        shell.user_ns[model_name] = form_cell
        assert value_name in shell.user_ns.keys()

        msg = {
            "msg": "update_form_cell",
            "form_cell_id": form_cell.id,
            "id": form_cell.id,
            "label": "",
            "model_variable_name": model_name,
            "value_variable_name": value_name,
            "variable_type": "number",
            "value": 50,
            "settings": {},
            "execution_trigger_behavior": "change_variable_only",
            "input_type": "slider",
            "extra_property": "foobar",
        }
        handle_msg(msg, sample_comm)

        updated_form_cell = shell.user_ns[model_name]
        assert updated_form_cell.value == 50
        assert shell.user_ns[value_name] == 50

    def test_update_datetime_form_cell(self, sample_comm: Comm):
        """
        Same as the test above, but for datetime form cells, where we include converting the
        value to a datetime object.
        """
        model_name = "dt_model"
        value_name = "dt"
        form_cell = Datetime(value_variable_name=value_name, settings={})
        shell = get_ipython_shell()
        shell.user_ns[model_name] = form_cell
        assert value_name in shell.user_ns.keys()

        msg = {
            "msg": "update_form_cell",
            "form_cell_id": form_cell.id,
            "id": form_cell.id,
            "label": "",
            "model_variable_name": model_name,
            "value_variable_name": value_name,
            "variable_type": "string",
            "value": "2020-01-01T00:00",
            "settings": {},
            "execution_trigger_behavior": "change_variable_only",
            "input_type": "datetime",
            "extra_property": "foobar",
        }
        handle_msg(msg, sample_comm)

        updated_form_cell = shell.user_ns[model_name]
        assert updated_form_cell.value == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
        assert shell.user_ns[value_name] == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
