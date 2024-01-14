import ctypes, bpy, gpu
import threading

# this runs from f3d_render_engine/__init__.py
# shader paths must also be relative to this directory
f3dlib: ctypes.CDLL = ctypes.CDLL("./modules/f3d_renderer_lib.dll", winmode=0)


def init_renderer() -> threading.Thread:
    x = threading.Thread(target=run_renderer, args=())
    x.start()
    return x


def stop_renderer():
    pass
    # f3dlib.end()


def run_renderer():
    print("Running main...")
    f3dlib.main()


def view_draw(buffer: gpu.types.Buffer, width: int, height: int):
    f3dlib.draw(buffer, width, height)


def view_update():
    pass


def test_ctypes(context: bpy.types.Context):
    dir(f3dlib)
    print("Hello CTypes!")
    f3dlib.test()
    x = threading.Thread(target=run_renderer, args=())
    x.start()
