# Based on https://github.com/huutaiii/blender-custom-render-engine
import os, sys

if os.name == "nt":
    delimiter = "\\"
if os.name == "posix":
    delimiter = "/"
if not delimiter:
    raise RuntimeError("Platform not supported")
names = __file__.split(delimiter)
path = delimiter.join(names[: len(names) - 1])

sys.path.append(path)
os.chdir(path)

from .modules import render_engine, operators, material


def render_engine_register():
    render_engine.register()
    operators.register()
    material.register()


def render_engine_unregister():
    render_engine.unregister()
    operators.unregister()
    material.unregister()
