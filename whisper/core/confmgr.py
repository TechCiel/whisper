"""
This module provides tools for configuration management.
"""
import typing as t
import importlib

from . import current_app
from .provider import BaseProvider

__all__ = ['Config', 'load', 'require']


class Config:
    """Multi level dict with attributes proxied to dict keys"""
    _config: dict[str, t.Any]

    def __init__(self, config: t.Optional[dict[str, t.Any]] = None) -> None:
        """Construct from existing or empty dict"""
        if config is None:
            config = {}
        # self._config = xxx without calling __setattr__
        self.__dict__['_config'] = config.copy()

    def __contains__(self, key: str) -> bool:
        """Check option existence"""
        return key in self._config

    def __getitem__(self, key: str) -> t.Any:
        """Returns value if option exists, defaults to nesting Config"""
        if key not in self._config:
            self._config[key] = Config()
        return self._config[key]

    def __setitem__(self, key: str, value: t.Any) -> None:
        """Sets option value"""
        self._config[key] = value

    def __getattr__(self, key: str) -> t.Any:
        """Proxy to __getitem__"""
        return self[key]

    def __setattr__(self, key: str, value: t.Any) -> None:
        """Proxy to __setitem__"""
        self[key] = value


def load(plugin: str) -> None:
    """Loads specific plugin and its default config, and register provider"""
    current_app.logger.info(f'Loading {plugin}')
    if plugin not in current_app.c:
        current_app.c[plugin] = Config()
    # import ..'module_name'.config as mod
    mod = importlib.import_module(
        '..'+plugin+'.config',
        package=__package__,
    )
    if 'provider' in mod.__dict__ and issubclass(mod.provider, BaseProvider):
        current_app.logger.info(
            f'Registering provider {plugin}: {mod.provider}',
        )
        current_app.p[plugin] = mod.provider()


def require(plugin: str) -> None:
    """Check if a specified module is already lodaed, raise if not"""
    if plugin not in current_app.c:
        raise NameError(f'{plugin} is required but not found')
