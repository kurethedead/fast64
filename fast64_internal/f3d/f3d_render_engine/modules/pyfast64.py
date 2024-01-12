import ctypes, bpy
import threading

# this runs from f3d_render_engine/__init__.py
# shader paths must also be relative to this directory
f3dlib = ctypes.CDLL("./modules/f3d_renderer_lib.dll")


def run_renderer():
    print("Running main...")
    f3dlib.main()


def test_ctypes(context: bpy.types.Context):
    dir(f3dlib)
    print("Hello CTypes!")
    f3dlib.test()
    x = threading.Thread(target=run_renderer, args=())
    x.start()
