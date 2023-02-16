import json
import sys
from typing import Any, Optional, Union

from pydantic import BaseModel

from sidecar_comms.shell import get_ipython_shell


class VariableModel(BaseModel):
    name: str
    type: str
    docstring: Optional[str]
    module: Optional[str]
    sample_value: Any  # may be the full value if small enough, only truncated for larger values
    size: Optional[Union[int, tuple]]
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


def variable_shape(value: Any) -> Optional[tuple]:
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


def variable_size(value: Any) -> Optional[Union[int, tuple]]:
    """Returns the size of a variable.

    For iterables, this returns the length / number of items.
    For matrix-like objects, this returns a tuple of the number of rows/columns, similar to .shape.
    """
    if hasattr(value, "__len__"):
        return len(value)

    if (shape := variable_shape(value)) is not None:
        return shape

    if (size := getattr(value, "size", None)) is None:
        return
    if isinstance(size, int):
        return size
    if isinstance(size, tuple):
        return size[0]


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


def variable_sample_value(value: Any, max_length: int = 1000) -> Any:
    """Returns a short representation of a value."""
    sample_value = None

    container_types = [list, set, frozenset, tuple]
    if isinstance(value, tuple(container_types)):
        sample_items = [
            variable_sample_value(item, max_length=max_length) for item in list(value)[:5]
        ]
        container_type = type(value)
        sample_value = container_type(sample_items)

    elif isinstance(value, dict):
        sample_value = value.keys()

    elif variable_size_bytes(value) > max_length:
        sample_value = f"{value!r}"[:max_length] + "..."

    try:
        json.dumps(sample_value)
        return sample_value
    except ValueError:
        # can't JSON serialize; stringify it and move on
        return f"{sample_value!r}"[:max_length]


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
            size=variable_size(value),
            size_bytes=variable_size_bytes(value),
            **basic_props,
        )
    except Exception as e:
        basic_props["error"] = str(e)

    return VariableModel(**basic_props)


def get_kernel_variables(skip_prefixes: list = None):
    """Returns a list of variables in the kernel."""
    variables = dict(get_ipython_shell().user_ns)

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


def rename_kernel_variable(old_name: str, new_name: str) -> str:
    """Renames a variable in the kernel."""
    ipython = get_ipython_shell()
    try:
        if new_name:
            ipython.user_ns[new_name] = ipython.user_ns[old_name]
        del ipython.user_ns[old_name]
        return "success"
    except Exception as e:
        return str(e)


def set_kernel_variable(name: str, value: Any) -> str:
    """Sets a variable in the kernel."""
    try:
        get_ipython_shell().user_ns[name] = value
        return "success"
    except Exception as e:
        return str(e)
