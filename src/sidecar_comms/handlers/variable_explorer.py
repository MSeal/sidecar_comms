import json
import sys
from typing import Any, Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


class VariableModel:
    name: str
    value: Any

    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

    @property
    def type(self):
        return type(self.value).__name__

    @property
    def size(self):
        if hasattr(self.value, "__len__"):
            return len(self.value)
        if hasattr(self.value, "size"):
            return self.value.size

    @property
    def size_bytes(self):
        try:
            return sys.getsizeof(self.value)
        except Exception:
            pass
        # may be a pandas object
        # TODO: add extra pandas object handlers
        try:
            return self.value.memory_usage().sum()
        except Exception:
            pass

    @property
    def sample_value(self):
        """Returns a short representation of a value."""
        if isinstance(self.value, list):
            return self.value[:5]
        if isinstance(self.value, dict):
            return self.value.keys()
        if self.size_bytes > 1000:
            return f"{self.value!r}"[:1000] + "..."

        try:
            json.dumps(self.value)
            return self.value
        except Exception:
            # non-JSON serializable
            return f"{self.value!r}"[:1000]

    def dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.sample_value,
            "type": self.type,
            "size": self.size,
            "size_bytes": self.size_bytes,
        }


def get_kernel_variables(
    skip_prefixes: list = None, ipython_shell: Optional[InteractiveShell] = None
):
    """Returns a list of variables in the kernel."""
    ipython = ipython_shell or get_ipython()
    variables = dict(ipython.user_ns)

    skip_prefixes = skip_prefixes or [
        "_",
        "In",
        "Out",
        "get_ipython",
        "exit",
        "quit",
        "open",
    ]
    variable_types = {}
    for name, value in variables.items():
        if name.startswith(tuple(skip_prefixes)):
            continue
        variable_types[name] = VariableModel(
            name=name,
            value=value,
        ).dict()
    return variable_types


def rename_kernel_variable(
    old_name: str,
    new_name: str,
    ipython_shell: Optional[InteractiveShell] = None,
) -> str:
    """Renames a variable in the kernel."""
    ipython = ipython_shell or get_ipython()
    try:
        if new_name:
            ipython.user_ns[new_name] = ipython.user_ns[old_name]
        del ipython.user_ns[old_name]
        return "success"
    except Exception as e:
        return str(e)


def set_kernel_variable(
    name: str,
    value: Any,
    ipython_shell: Optional[InteractiveShell] = None,
) -> str:
    """Sets a variable in the kernel."""
    ipython = ipython_shell or get_ipython()
    try:
        ipython.user_ns[name] = value
        return "success"
    except Exception as e:
        return str(e)
