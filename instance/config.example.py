"""
This is an example config file of whisper blog engine
Please create `config.py` in your instance folder

Use `load(plugin: str)` to load plugins by imported package name

Copy lines from `plugin_name/config.py` to override default configuration
"""
from whisper.core import app, load

# load a plugin (`core` is also a plugin)
load('core')

# set an option
app.c.section1.section2.option3 = 'value4'
