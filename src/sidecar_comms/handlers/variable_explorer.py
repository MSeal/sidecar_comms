import json
import sys
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from sidecar_comms.shell import get_ipython_shell

MAX_STRING_LENGTH = 1000
CONTAINER_TYPES = [list, set, frozenset, tuple]


class VariableModel(BaseModel):
    name: str
    type: str
    docstring: Optional[str]
    module: Optional[str]
    sample_value: Any  # may be the full value if small enough, only truncated for larger values
    size: Optional[Union[int, tuple]]
    size_bytes: Optional[int]
    extra: dict = Field(default_factory=dict)
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


def variable_module(value: Any) -> str:
    return getattr(value, "__module__", "")


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
    if (shape := variable_shape(value)) is not None:
        return shape

    if hasattr(value, "__len__"):
        return len(value)

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


def variable_sample_value(value: Any, max_length: Optional[int] = None) -> Any:
    """Returns a short representation of a value."""
    sample_value = value
    max_length = max_length or MAX_STRING_LENGTH

    if isinstance(value, tuple(CONTAINER_TYPES)):
        sample_items = [
            variable_sample_value(item, max_length=max_length) for item in list(value)[:5]
        ]
        container_type = type(value)
        # convert back to original type if we're only showing some items
        sample_value = container_type(sample_items)

    if not is_json_serializable(sample_value):
        return

    if variable_size_bytes(sample_value) > max_length:
        sample_value = repr(sample_value)[:max_length] + "..."

    return sample_value


def variable_extra_properties(value: Any) -> Optional[dict]:
    """Handles extracting/generating additional properties for a variable
    based on supported types.
    """
    extra = {}

    if variable_type(value) == "DataFrame":
        if hasattr(value, "columns"):
            columns = list(value.columns)[:100]
            extra["columns"] = columns

            if hasattr(value, "dtypes"):
                if variable_module(value).startswith("pandas") or isinstance(value.dtypes, dict):
                    dtypes = dict(value.dtypes).values()
                else:
                    dtypes = list(value.dtypes)

                # ensure we can still pass the string dtype through,
                # since they aren't JSON serializable
                extra["dtypes"] = {
                    column: str(dtype).lower() for column, dtype in zip(columns, dtypes)
                }

        if hasattr(value, "index"):
            extra["index"] = list(value.index)[:100]

    if variable_type(value) == "dict":
        extra["keys"] = list(value.keys())[:100]

    return extra


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
        "module": variable_module(value),
    }

    # in the event we run into any parsing/validation errors,
    # we'll still send the variable model with basic properties
    # and an error message
    try:
        return VariableModel(
            sample_value=variable_sample_value(value),
            size=variable_size(value),
            size_bytes=variable_size_bytes(value),
            extra=variable_extra_properties(value),
            **basic_props,
        )
    except Exception as e:
        basic_props["error"] = f"{e!r}"

    return VariableModel(**basic_props)


def is_json_serializable(value: Any) -> bool:
    """Returns True if a value is JSON serializable."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        # either one of these may appear:
        # - TypeError: X is not JSON serializable
        # - ValueError: Can't clean for JSON: X
        # and we won't try to get a string repr here since that could
        # potentially take a while depending on any custom __repr__ methods
        return False


def json_clean(value: Any, max_length: Optional[int] = None) -> Optional[str]:
    """Ensures a value is JSON serializable, converting to a string if necessary.

    Recursively cleans values of dictionaries, and items in lists, sets, and tuples
    if necessary.
    """
    max_length = max_length or MAX_STRING_LENGTH

    if isinstance(value, dict):
        value = {k: json_clean(v) for k, v in value.items()}
    elif isinstance(value, tuple(CONTAINER_TYPES)):
        container_type = type(value)
        value = container_type([json_clean(v) for v in value])

    if is_json_serializable(value):
        return value


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
    variable_data = {}
    for name, value in variables.items():
        if name.startswith(tuple(skip_prefixes)):
            continue
        variable_model = variable_to_model(name=name, value=value)
        cleaned_variable_model_dict = {k: json_clean(v) for k, v in variable_model.dict().items()}
        variable_data[name] = cleaned_variable_model_dict
    return variable_data


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
