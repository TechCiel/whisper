"""
This module implements TOTP authenticator, relying an authenticator app.
"""
from . import AuthProvider

__all__ = ['TOTPAuth']


class TOTPAuth(AuthProvider):
    """Not Implemented"""

    def render(self, name: str) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def check(self) -> bool:
        """Not Implemented"""
        raise NotImplementedError
