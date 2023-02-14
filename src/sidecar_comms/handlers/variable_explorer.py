import json
import sys
from typing import Any, Optional, Tuple

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from pydantic import BaseModel


class VariableModel(BaseModel):
    name: str
    type: str
    docstring: Optional[str]
    module: Optional[str]
    sample_value: Any  # may be the full value if small enough, only truncated for larger values
    shape: Optional[Tuple]
    size: Optional[int]
    size_bytes: Optional[int]
    error: Optional[str]


def variable_docstring(value: Any) -> Optional[str]:
    """Returns the docstring of a variable."""
    if (doc := getattr(value, "__doc__", None)) is None:
        return
    if not isinstance(doc, str):
        return
    return doc[:5000]


def variable_type(value: Any) -> str:
    return type(value).__name__


def variable_size(value: Any) -> Optional[int]:
    """Returns the size (1-dimensional; length) of a variable."""
    if hasattr(value, "__len__"):
        return len(value)
    if (size := getattr(value, "size", None)) is None:
        return
    if isinstance(size, int):
        return size
    if isinstance(size, tuple):
        return size[0]


def variable_shape(value: Any) -> Optional[int]:
    """Returns the shape (n-dimensional; rows, columns, ...) of a variable."""
    if (shape := getattr(value, "shape", None)) is None:
        return
    if not isinstance(shape, tuple):
        return
    if not shape:
        return
    if not isinstance(shape[0], int):
        return
    return shape


def variable_size_bytes(value: Any) -> Optional[int]:
    """Returns the size of a variable in bytes."""
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
        # TODO: come back to this and maybe recursively check
        # items in container
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
    """Gathers properties of a variable to send to the sidecar through
    a variable explorer comm message.
    Should always have `name` and `type` properties; `error` will show
    conversion/inspection errors for size/size_bytes/sample_value.
    """
    basic_props = {
        "name": name,
        "docstring": variable_docstring(value),
        "type": variable_type(value),
        "module": getattr(value, "__module__", None),
    }

    # in the event we run into any parsing/validation errors,
    # we'll still send the variable model with basic properties
    # and an error message
    try:
        return VariableModel(
            sample_value=variable_sample_value(value),
            shape=variable_shape(value),
            size=variable_size(value),
            size_bytes=variable_size_bytes(value),
            **basic_props,
        )
    except Exception as e:
        basic_props["error"] = str(e)

    return VariableModel(**basic_props)


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
