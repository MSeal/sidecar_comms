import modin.pandas as mpd
import pandas as pd
import polars as pl
import pytest

from sidecar_comms.handlers.variable_explorer import get_kernel_variables, variable_sample_value
from sidecar_comms.shell import get_ipython_shell


class TestGetKernelVariables:
    def test_skip_prefixes(self):
        """Test that the skip_prefixes are working as expected."""
        shell = get_ipython_shell()
        shell.user_ns["foo"] = 123
        shell.user_ns["bar"] = 456
        shell.user_ns["_baz"] = 789
        shell.user_ns["SECRET_abc"] = 123
        variables = get_kernel_variables(skip_prefixes=["_", "SECRET_"])
        # initial run should be empty based on the skip_prefixes
        assert isinstance(variables, dict)
        assert "foo" in variables
        assert "bar" in variables
        assert "_baz" not in variables
        assert "SECRET_abc" not in variables

    def test_integer(self):
        """Test that a basic integer variable is added to the variables
        response with the correct information."""
        variable_name = "foo"
        variable_value = 123
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        # add a basic integer variable
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "int"
        assert variables[variable_name]["size"] is None
        assert variables[variable_name]["sample_value"] == variable_value

    def test_list(self):
        """Test that a basic list variable is added to the variables
        response with the correct information."""
        variable_name = "bar"
        variable_value = [1, 2, 3]
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "list"
        assert variables[variable_name]["size"] == 3
        assert variables[variable_name]["sample_value"] == variable_value

    def test_dict(self):
        """Test that a basic dict variable is added to the variables
        response with the correct information."""
        variable_name = "baz"
        variable_value = {"a": 1, "b": 2, "c": 3, "d": 4}
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "dict"
        assert variables[variable_name]["size"] == 4
        assert variables[variable_name]["sample_value"] == variable_value

    def test_long_string(self):
        """Test that a long string variable is added to the variables
        response with the correct information."""
        variable_name = "qux"
        variable_value = "ABC" * 5000
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "str"
        assert variables[variable_name]["size"] == len(variable_value)
        assert variables[variable_name]["sample_value"] == variable_sample_value(variable_value)

    def test_fn(self):
        """Test that a variable assigned to a function is added to the variables
        response with the correct information.
        """

        def foo():
            pass

        variable_name = "test_fn"
        variable_value = foo
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "function"
        assert variables[variable_name]["size"] is None
        # functions aren't JSON-serializable, so the sample value should be None
        assert variables[variable_name]["sample_value"] is None

    def test_fn_in_list(self):
        """Test that a variable assigned to a function in a list is added
        to the variables response with the correct information.
        """

        def foo():
            pass

        variable_name = "test_fn_in_list"
        variable_value = [foo]
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name]["name"] == variable_name
        assert variables[variable_name]["type"] == "list"
        assert variables[variable_name]["size"] == 1
        assert isinstance(variables[variable_name]["sample_value"], list)
        # functions aren't JSON-serializable, so the first item in the sample value should be None
        assert variables[variable_name]["sample_value"][0] is None

    def test_broken_property(self):
        """Test that a variable with an unexpected/unhandled property type will
        populate the `error` property in the VariableModel message.
        """

        class Foo:
            def __len__(self):
                raise Exception("I'm broken!")

        variable_name = "test_foo"
        variable_value = Foo()
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        assert variable_name in variables
        assert variables[variable_name].get("error") is not None


class TestDataFrameVariables:
    @pytest.fixture
    def pandas_dataframe(self):
        """Fixture to provide a pandas DataFrame."""
        return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    @pytest.fixture
    def polars_dataframe(self, pandas_dataframe: pd.DataFrame):
        """Fixture to provide a polars DataFrame."""
        return pl.from_pandas(pandas_dataframe)

    @pytest.fixture
    def modin_dataframe(self, pandas_dataframe: pd.DataFrame):
        """Fixture to provide a modin DataFrame."""
        return mpd.DataFrame(pandas_dataframe)

    def test_dataframe_extras(
        self,
        pandas_dataframe,
        polars_dataframe,
        modin_dataframe,
    ):
        """Test that a variable assigned to a non-pandas DataFrame will provide
        column/dtype information, if available.
        """
        variables = {
            "df": pandas_dataframe,
            "pdf": polars_dataframe,
            "mdf": modin_dataframe,
        }
        get_ipython_shell().user_ns.update(variables)

        variables = get_kernel_variables()
        for variable_name in variables.keys():
            assert variable_name in variables
            assert variables[variable_name]["type"] == "DataFrame"
            assert variables[variable_name]["error"] is None
            assert isinstance(variables[variable_name]["extra"]["columns"], list)
            assert isinstance(variables[variable_name]["extra"]["dtypes"], dict)
            assert "a" in variables[variable_name]["extra"]["columns"]
            assert "a" in variables[variable_name]["extra"]["dtypes"]
