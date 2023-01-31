"""
 - This is going to move into its own package, here for now to speed up development of Form cells
 - Does not observe changes to mutable objects (model.list_thing.append()), will plan to try and
   add support for that but it's a big task. See following issues and links:
   - Pydantic validate types in mutable lists: https://github.com/pydantic/pydantic/issues/496
   - Traitlets observe dict change: https://github.com/ipython/traitlets/issues/495

Use:

class Foo(ObservableModel):
    a: int = 3

f = Foo()
f
>>> Foo(a=3)

def printer(change: Change):
    print(f"Field {change.name} changed from {change.old} to {change.new}")

obs = f.observe(printer)
obs
>>> Observer(names=['a'], fn=<function printer at 0x7f50dc6a0e50>, args=[], kwargs={})

f.a = 4
f
>>> Field a changed from 3 to 4
    Foo(a=4)
"""
from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Union

from pydantic import BaseModel, PrivateAttr


class Change(BaseModel):
    name: str
    old: Any
    new: Any


class Observer(BaseModel):
    names: List[str]
    fn: Callable
    args: List = []
    kwargs: Dict = {}


class ObservableModel(BaseModel):
    # The same Observer might be listed multiple times. For instance if you have a model
    # with two fields and .observe(<callback>, names=None), it will create an Observer
    # that will be registered on both fields. Inspecting ._observers will show you a dictionary
    # of {field1: [your_obs], field2: [your_obs]}
    _observers: DefaultDict[str, List[Observer]] = PrivateAttr(
        default_factory=lambda: defaultdict(list)
    )

    class Config:
        validate_assignment = True

    def __setattr__(self, name, value):
        if name not in self._observers:
            super().__setattr__(name, value)
        else:
            old_value = getattr(self, name)
            super().__setattr__(name, value)
            if old_value != value:
                change = Change(name=name, old=old_value, new=value)
                for obs in self._observers[name]:
                    obs.fn(change, *obs.args, **obs.kwargs)

    def observe(
        self,
        fn: Callable,
        names: Optional[Union[str, List[str]]] = None,
        *args,
        **kwargs,
    ) -> Observer:
        """
        Attach a callback when the value of one or more fields in this model change.
         - if name is None, the callback is triggered on all fields
         - if name is a string, callback is registered for a single field
         - if name is a list of strings, callback is registered on those specific fields
        """
        if names is None:
            names = list(self.__fields__)
        elif isinstance(names, str):
            names = [names]
        obs = Observer(names=names, fn=fn, args=args, kwargs=kwargs)
        for name in names:
            self._observers[name].append(obs)
        return obs

    def remove_observer(self, obs: Observer) -> None:
        for name, obs_list in self._observers.items():
            if obs in obs_list:
                self._observers[name].remove(obs)
