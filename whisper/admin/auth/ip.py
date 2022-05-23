"""
This module implements IP authenticator, relying an IP network list.
"""
from . import AuthProvider

__all__ = ['IPAuth']


class IPAuth(AuthProvider):
    """Not Implemented"""

    def render(self, name: str) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def check(self) -> bool:
        """Not Implemented"""
        raise NotImplementedError
