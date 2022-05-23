"""
This module implements dummy authenticator, which is always passing.
"""
from . import AuthProvider

__all__ = ['DummyAuth']


class DummyAuth(AuthProvider):
    """Always success directly"""

    def render(self, name: str) -> str:
        """Mark as success in frontend"""
        return f"""
<script>
window.addEventListener('load', async function() {{
    try_auth('{name}')
}})
</script>"""

    def check(self) -> bool:
        """Always success"""
        return True
