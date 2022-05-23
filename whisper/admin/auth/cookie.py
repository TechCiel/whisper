"""
This module implements cookie authenticator, relying a secret cookie.
"""
from flask import request, url_for

from . import AuthProvider

__all__ = ['CookieAuth']


class CookieAuth(AuthProvider):
    """Check if a cookie present to authenticate"""

    def __init__(self, key: str, value: str) -> None:
        """Set cookie name and value"""
        self.key = key
        self.value = value

    def render(self, name: str) -> str:
        """Perform a check if cookie exist by preflighting in frontend"""
        return f"""
<script>
window.addEventListener('load', async function() {{
    let response = await fetch('{ url_for('auth.check', name=name) }', {{ method: 'POST'}})
    if (response.ok) try_auth('{name}')
}})
</script>"""

    def check(self) -> bool:
        """Check cookie content"""
        return request.cookies.get(self.key) == self.value
