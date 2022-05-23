"""
This module implements WebAuthn authenticator, relying an crypto key.
"""
from . import AuthProvider

__all__ = ['WebAuthnAuth']


class WebAuthnAuth(AuthProvider):
    """Not Implemented"""

    def render(self, name: str) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def check(self) -> bool:
        """Not Implemented"""
        raise NotImplementedError
