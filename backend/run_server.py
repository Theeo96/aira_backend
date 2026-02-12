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
            handle = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE = -10
            
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
    # 1. CPU 코어 수 확인
    try:
        cores = multiprocessing.cpu_count()
    except NotImplementedError:
        cores = 4 # 기본값 fallback
    
    # 2. 워커 수 결정 (CPU 코어 수와 1:1 매핑 권장)
    # 너무 많이 띄우면 컨텍스트 스위칭 오버헤드 발생
    workers = cores 
    
    # 개발 모드(Reload)일 때는 워커 1개로 제한 (Reload는 멀티 워커 지원 안함)
    if "--reload" in sys.argv:
        workers = 1
        print(f"[Run] Development Mode: Starting with {workers} worker (Reload Enabled)")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            workers=workers,
            reload=True,
            use_colors=False
        )
    else:
        print(f"[Run] Production Mode: Starting with {workers} workers on {cores} cores...")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            workers=workers,
            use_colors=False
        )

if __name__ == "__main__":
    main()
