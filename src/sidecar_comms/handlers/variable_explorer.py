import sys
from typing import Any, Optional

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


def short_value(value: Any) -> str:
    """Returns a short representation of a value."""
    if isinstance(value, list):
        return value[:5]
    if isinstance(value, dict):
        return value.keys()
    if sys.getsizeof(value) > 1000:
        return f"{value!r}"[:100] + "..."
    return value


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
        variable_types[name] = {
            "name": name,
            "type": type(value).__name__,
            "size": len(value) if hasattr(value, "__len__") else 1,
            "value": short_value(value),
        }
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
