# sidecar_comms

Enabling more flexible comm paths between the kernel and the kernel sidecar.

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