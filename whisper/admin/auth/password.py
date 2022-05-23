"""
This module implements password authenticator, checking against a hash.
"""
import secrets
import hashlib
from flask import request

from . import AuthProvider

__all__ = ['PasswordAuth']


class PasswordAuth(AuthProvider):
    """Check if the password match the hash"""

    def __init__(self, hashed: str, display: str = 'Password') -> None:
        """Set the hash, frontend display, and a random field name"""
        self.hashed = hashed
        self.display = display
        self.field = f'password_{secrets.token_hex(8)}'

    def render(self, name: str) -> str:
        """Render form input"""
        return f"""
<h2>{self.display}</h2>
<input form="auth" name="{self.field}" type="password" autocomplete="on">
<hr>
"""

    def check(self) -> bool:
        """Check against hash"""
        password = request.form.get(self.field, '', type=str)
        return PasswordAuth.hash(password) == self.hashed

    @staticmethod
    def hash(password: str) -> str:
        """Calulate SHA-256 for password string"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
