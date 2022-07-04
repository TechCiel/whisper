"""
Defaults of the file provider.

DO NOT EDIT THIS FILE! copy lines into instance configuration to override.
"""
from whisper.core import app, require

from . import FileProvider as provider  # pylint: disable=unused-import

require('core')

# the renderer to to render file list
# can be override by post meta 'file:main'
app.c.file.main = 'main'

app.c.file.css = ''
# Exmaple:
# current_app.c.file.css = """<style>
# ul {
#     ...
# }
# </style>"""

app.c.file.js = ''
# Exmaple:
# current_app.c.file.js = """<script>
# // code goes here ...
# </script>"""
