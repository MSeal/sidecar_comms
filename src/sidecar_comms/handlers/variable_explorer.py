import json
import sys
from typing import Any, Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from pydantic import BaseModel


class VariableModel(BaseModel):
    name: str
    value: Any
    type: str
    size: Optional[int]
    size_bytes: Optional[int]


def variable_type(value: Any) -> str:
    return type(value).__name__


def variable_size(value: Any) -> Optional[int]:
    if hasattr(value, "__len__"):
        return len(value)
    if hasattr(value, "size"):
        return value.size


def variable_size_bytes(value: Any) -> Optional[int]:
    try:
        return sys.getsizeof(value)
    except Exception:
        pass
    # may be a pandas object
    # TODO: add extra pandas object handlers
    try:
        return value.memory_usage().sum()
    except Exception:
        pass


def variable_sample_value(value: Any) -> Any:
    """Returns a short representation of a value."""
    if isinstance(value, list):
        return value[:5]
    if isinstance(value, dict):
        return value.keys()
    if variable_size_bytes(value) > 1000:
        return f"{value!r}"[:1000] + "..."
    try:
        json.dumps(value)
        return value
    except Exception:
        # non-JSON serializable
        return f"{value!r}"[:1000]


def variable_to_model(name: str, value: Any) -> VariableModel:
    return VariableModel(
        name=name,
        value=variable_sample_value(value),
        type=variable_type(value),
        size=variable_size(value),
        size_bytes=variable_size_bytes(value),
    )


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
        variable_model = variable_to_model(name=name, value=value)
        variable_types[name] = variable_model.dict()
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