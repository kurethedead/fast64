# Based on https://github.com/huutaiii/blender-custom-render-engine
import os, sys

# This code is needed to load shaders from folder
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

from .modules import render_engine, operators, material, fast64_core


def render_engine_register():
    render_engine.register()
    operators.register()
    material.register()


def render_engine_unregister():
    render_engine.unregister()
    operators.unregister()
    material.unregister()
