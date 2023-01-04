# sidecar_comms

<p align="center">
Enabling more flexible comm paths between the kernel and the kernel sidecar.
</p>

<p align="center">
<a href="https://github.com/noteable-io/sidecar_comms/actions/workflows/ci.yaml">
    <img src="https://github.com/noteable-io/sidecar_comms/actions/workflows/ci.yaml/badge.svg" alt="CI" />
</a>
<a href="https://codecov.io/gh/noteable-io/sidecar_comms" > 
 <img src="https://codecov.io/gh/noteable-io/sidecar_comms/branch/main/graph/badge.svg?token=XGXSTD3GSI" alt="codecov code coverage"/> 
 </a>
<!-- <img alt="PyPI - License" src="https://img.shields.io/pypi/l/sidecar_comms" />
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/sidecar_comms" />
<img alt="PyPI" src="https://img.shields.io/pypi/v/sidecar_comms"> -->
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

---------

## Requirements

Python 3.8+

## Installation

### Poetry

```shell
poetry add dx
```

### Pip
```shell
pip install dx
```

## Usage
```python
import sidecar_comms as sc
```

### Outbound Comms (Kernel -> Sidecar)
The `CommManager` is responsible for opening comms with the sidecar. 
As an example, to open a comm from the sidecar to the kernel to allow the kernel to keep track of available cell IDs in the notebook document:
```python
mgr = sc.comm_manager()
cell_id_comm = mgr.open_comm("cell_ids")
```
Then, the `cell_id_comm.value` (a traitlet) would allow the user to see a list of available cell IDs at any moment.
```python
>>> cell_id_comm.value
['3b816f9f',
 'ea2b4ec5-055d-4d6a-9542-0c6b32e9af4c',
 '0e887fcf-56dd-4914-aaef-4d5741d15ac5',
 'f32c374a-7375-4203-8343-954cf0e5b11b',
 '9359c010-094f-4718-904e-2632f169d430']
```

### Inbound Comms (Sidecar -> Kernel)
In progress


## References
- https://jupyter-notebook.readthedocs.io/en/stable/comms.html


## Contributing

See [CONTRIBUTING.md](https://github.com/noteable-io/sidecar_comms/blob/main/CONTRIBUTING.md).

## Code of Conduct

We follow the noteable.io [code of conduct](https://github.com/noteable-io/sidecar_comms/blob/main/CODE_OF_CONDUCT.md).

## LICENSE

See [LICENSE.md](https://github.com/noteable-io/sidecar_comms/blob/main/LICENSE.md).


-------

<p align="center">Open sourced with ❤️ by <a href="https://noteable.io">Noteable</a> for the community.</p>

<img href="https://pages.noteable.io/private-beta-access" src="https://assets.noteable.io/github/2022-07-29/noteable.png" alt="Boost Data Collaboration with Notebooks">