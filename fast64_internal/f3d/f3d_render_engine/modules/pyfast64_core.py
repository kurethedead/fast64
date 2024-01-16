import ctypes, bpy, gpu, sys
import threading

# this runs from f3d_render_engine/__init__.py
# shader paths must also be relative to this directory
if sys.platform.startswith("win32"):
    module_path = "./modules/fast64_core.pyd"
else:
    module_path = "./modules/fast64_core.so"

fast64_core: ctypes.CDLL = ctypes.CDLL(module_path, winmode=0)


def run_renderer(rendererID):
    fast64_core.start_renderer(rendererID)


def init_renderer(rendererID: int) -> threading.Thread:
    x = threading.Thread(target=run_renderer, args=(rendererID,))
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
