from collections import defaultdict

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
        get_ipython_shell().user_ns["foo"] = 123
        variables = get_kernel_variables()
        # add a basic integer variable
        assert "foo" in variables
        assert variables["foo"]["name"] == "foo"
        assert variables["foo"]["type"] == "int"
        assert variables["foo"]["size"] is None
        assert variables["foo"]["sample_value"] == 123

    def test_list(self):
        """Test that a basic list variable is added to the variables
        response with the correct information."""
        get_ipython_shell().user_ns["bar"] = [1, 2, 3]
        variables = get_kernel_variables()
        # add a list variable
        assert "bar" in variables
        assert variables["bar"]["name"] == "bar"
        assert variables["bar"]["type"] == "list"
        assert variables["bar"]["size"] == 3
        assert variables["bar"]["sample_value"] == [1, 2, 3]

    def test_dict(self):
        """Test that a basic dict variable is added to the variables
        response with the correct information."""
        get_ipython_shell().user_ns["baz"] = {"a": 1, "b": 2, "c": 3, "d": 4}
        variables = get_kernel_variables()
        # add a dict variable
        assert "baz" in variables
        assert variables["baz"]["name"] == "baz"
        assert variables["baz"]["type"] == "dict"
        assert variables["baz"]["size"] == 4
        assert variables["baz"]["sample_value"] == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_long_string(self):
        """Test that a long string variable is added to the variables
        response with the correct information."""
        variable_name = "qux"
        variable_value = "ABC" * 5000
        get_ipython_shell().user_ns[variable_name] = variable_value
        variables = get_kernel_variables()
        # add a long string variable
        assert "qux" in variables
        assert variables["qux"]["name"] == "qux"
        assert variables["qux"]["type"] == "str"
        assert variables["qux"]["size"] == 15000
        assert variables["qux"]["sample_value"] == variable_sample_value(variable_value)

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
        assert variables[variable_name]["sample_value"].startswith("<function")

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
        assert isinstance(variables[variable_name]["sample_value"], list)
        assert variables[variable_name]["sample_value"][0].startswith("<function")

    def test_broken_property(self):
        """Test that a variable with an unexpected/unhandled property type will
        populate the `error` property in the VariableModel message.
        """

        class Foo:
            def __len__(self):
                raise Exception("I'm broken!")

        get_ipython_shell().user_ns["test_dict"] = Foo()
        variables = get_kernel_variables()
        assert "test_dict" in variables
        assert variables["test_dict"].get("error") is not None
