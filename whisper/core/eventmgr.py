"""
This module provides tools for event (a.k.a. hook) management.
"""
import typing as t

from . import current_app

__all__ = ['EventManager', 'AnyDict', 'EventHandler']

AnyDict = dict[t.Any, t.Any]
EventHandler = t.Callable[[AnyDict], AnyDict]


class EventManager:
    """An event hook registry to callback functions when event is invoked"""

    def __init__(self) -> None:
        """Initialize empty registry"""
        self.registry: dict[str, list[EventHandler]] = {}

    def register(self, event: str, callback: EventHandler) -> None:
        """Register an EventHandler callback function to an event name"""
        current_app.e('core:event_regeister', locals())
        self.registry.setdefault(event, [])
        self.registry[event].append(callback)

    def __call__(self, event: str, arg: t.Optional[AnyDict] = None) -> AnyDict:
        """Invoke a event by name, call functions with args specified"""
        if arg is None:
            arg = {}
        for callback in self.registry.get(event, []):
            ret = callback(arg)
            if not isinstance(ret, dict):
                raise TypeError('event handler must return a dict')
            arg = ret
            if arg.pop('_stop', False):
                break
        return arg
