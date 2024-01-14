import ctypes, bpy, gpu
import threading

# this runs from f3d_render_engine/__init__.py
# shader paths must also be relative to this directory
fast64_core: ctypes.CDLL = ctypes.CDLL("./modules/fast64_cored.dll", winmode=0)


def run_renderer():
    fast64_core.start_renderer()


def init_renderer() -> threading.Thread:
    x = threading.Thread(target=run_renderer, args=())
    x.start()
    return x


def stop_renderer():
    fast64_core.end_renderer()


def view_draw(buffer: gpu.types.Buffer, width: int, height: int):
    fast64_core.view_draw(buffer, width, height)


def view_update():
    fast64_core.view_update()


def test_print(context: bpy.types.Context):
    fast64_core.print_hello()
