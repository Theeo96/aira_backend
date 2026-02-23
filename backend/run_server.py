import uvicorn
import os
import multiprocessing
import sys

import ctypes


def disable_quick_edit():
    # Windows Only: Disable QuickEdit Mode to prevent console hang
    if os.name == 'nt':
        try:
            kernel32 = ctypes.windll.kernel32
            mode = ctypes.c_ulong()
            handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE = -10

            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            # ENABLE_QUICK_EDIT_MODE = 0x0040
            # ENABLE_EXTENDED_FLAGS = 0x0080
            # We want to remove QUICK_EDIT, but keep EXTENDED_FLAGS
            mode.value &= ~0x0040
            mode.value |= 0x0080
            kernel32.SetConsoleMode(handle, mode)
            print("[System] Windows QuickEdit Mode Disabled (Prevent Hang)")
        except Exception as e:
            print(f"[System] Failed to disable QuickEdit: {e}")


def main():
    disable_quick_edit()

    # 1) Detect CPU cores
    try:
        cores = multiprocessing.cpu_count()
    except NotImplementedError:
        cores = 4

    # 2) Decide worker count
    # On Windows, multiprocessing workers can fail in some environments (WinError 5).
    # Keep default to 1 for stability unless explicitly overridden.
    if os.name == 'nt':
        workers = 1
    else:
        workers = cores

    workers_override = os.getenv("UVICORN_WORKERS")
    if workers_override:
        try:
            workers = max(1, int(workers_override))
        except ValueError:
            print(f"[Run] Ignoring invalid UVICORN_WORKERS='{workers_override}'")

    # Reload mode requires a single worker.
    if "--reload" in sys.argv:
        workers = 1
        print(f"[Run] Development Mode: Starting with {workers} worker (Reload Enabled)")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            workers=workers,
            reload=True,
            use_colors=False,
        )
    else:
        print(f"[Run] Production Mode: Starting with {workers} workers on {cores} cores...")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            workers=workers,
            use_colors=False,
        )


if __name__ == "__main__":
    main()
