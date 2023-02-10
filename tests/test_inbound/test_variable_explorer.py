from IPython.core.interactiveshell import InteractiveShell

from sidecar_comms.handlers.variable_explorer import get_kernel_variables, short_value


class TestGetKernelVariables:
    def test_skip_prefixes(self, get_ipython: InteractiveShell):
        """Test that the skip_prefixes are working as expected."""
        get_ipython.user_ns["foo"] = 123
        get_ipython.user_ns["bar"] = 456
        get_ipython.user_ns["_baz"] = 789
        get_ipython.user_ns["SECRET_abc"] = 123
        variables = get_kernel_variables(skip_prefixes=["_", "SECRET_"], ipython_shell=get_ipython)
        # initial run should be empty based on the skip_prefixes
        assert isinstance(variables, dict)
        assert "foo" in variables
        assert "bar" in variables
        assert "_baz" not in variables
        assert "SECRET_abc" not in variables

    def test_integer(self, get_ipython: InteractiveShell):
        """Test that a basic integer variable is added to the variables
        response with the correct information."""
        get_ipython.user_ns["foo"] = 123
        variables = get_kernel_variables(ipython_shell=get_ipython)
        # add a basic integer variable
        assert "foo" in variables
        assert variables["foo"]["name"] == "foo"
        assert variables["foo"]["type"] == "int"
        assert variables["foo"]["size"] == 1
        assert variables["foo"]["value"] == 123

    def test_list(self, get_ipython: InteractiveShell):
        """Test that a basic list variable is added to the variables
        response with the correct information."""
        get_ipython.user_ns["bar"] = [1, 2, 3]
        variables = get_kernel_variables(ipython_shell=get_ipython)
        # add a list variable
        assert "bar" in variables
        assert variables["bar"]["name"] == "bar"
        assert variables["bar"]["type"] == "list"
        assert variables["bar"]["size"] == 3
        assert variables["bar"]["value"] == [1, 2, 3]

    def test_dict(self, get_ipython: InteractiveShell):
        """Test that a basic dict variable is added to the variables
        response with the correct information."""
        get_ipython.user_ns["baz"] = {"a": 1, "b": 2, "c": 3, "d": 4}
        variables = get_kernel_variables(ipython_shell=get_ipython)
        # add a dict variable
        assert "baz" in variables
        assert variables["baz"]["name"] == "baz"
        assert variables["baz"]["type"] == "dict"
        assert variables["baz"]["size"] == 4
        assert variables["baz"]["value"] == {"a": 1, "b": 2, "c": 3, "d": 4}.keys()

    def test_long_string(self, get_ipython: InteractiveShell):
        """Test that a long string variable is added to the variables
        response with the correct information."""
        get_ipython.user_ns["qux"] = "ABC" * 5000
        variables = get_kernel_variables(ipython_shell=get_ipython)
        # add a long string variable
        assert "qux" in variables
        assert variables["qux"]["name"] == "qux"
        assert variables["qux"]["type"] == "str"
        assert variables["qux"]["size"] == 15000
        assert variables["qux"]["value"] == short_value("ABC" * 5000)
