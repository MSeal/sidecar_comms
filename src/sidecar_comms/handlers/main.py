from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


def get_kernel_variables():
    """Returns a list of variables in the kernel."""
    ipython = get_ipython()
    variables = dict(ipython.user_ns)
    variable_types = {name: str(type(value)) for name, value in variables.items()}
    return {
        "data": variable_types,
        "source": "sidecar_comms",
        "handler": "get_kernel_variables",
    }


def rename_kernel_variable(
    old_name: str,
    new_name: str,
    ipython_shell: InteractiveShell,
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
