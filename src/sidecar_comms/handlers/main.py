from IPython import get_ipython


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
