import ctypes
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

press_times = {}
timings = []

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

original_mode = wintypes.DWORD()
hStdin = kernel32.GetStdHandle(-10) 
hook = None
target_hwnd = None

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

def temizlik_yap():
    global hook, original_mode, hStdin
    if hook:
        user32.UnhookWindowsHookEx(hook)
        hook = None
    if hStdin and original_mode.value != 0:
        kernel32.SetConsoleMode(hStdin, original_mode)

def HookCallback(nCode, wParam, lParam):
    global target_hwnd
    if nCode >= 0:
        current_active_window = user32.GetForegroundWindow()
        if current_active_window != target_hwnd:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        kbd = KBDLLHOOKSTRUCT.from_address(lParam)
        
        if kbd.flags & 0x00000010 or kbd.flags & 0x00000001:
            return 1
            
        current_time = time.perf_counter()
        
        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            if kbd.vkCode not in press_times:
                press_times[kbd.vkCode] = current_time
        elif wParam in (WM_KEYUP, WM_SYSKEYUP):
            if kbd.vkCode in press_times:
                p_time = press_times.pop(kbd.vkCode)
                dwell_time = (current_time - p_time) * 1000
                timings.append((kbd.vkCode, round(dwell_time, 2)))
                
                if kbd.vkCode == 13: 
                    gelen_giris = timings[:-1]
                    sys.stdout.write(f"\n\n[ILK RITIM YAKALANDI]\n")
                    sys.stdout.write(f"Yazis Hizi Kalibiniz: {gelen_giris}\n")
                    sys.stdout.write("\nC:\\Users\\ortak>")
                    sys.stdout.flush()
                    timings.clear()
                    press_times.clear()
                    
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
pointer = HOOKPROC(HookCallback)

def main():
    global hook, original_mode, hStdin, target_hwnd
    
    target_hwnd = user32.GetForegroundWindow()
    user32.SetWindowTextW(target_hwnd, "C:\\Windows\\system32\\cmd.exe")

    kernel32.GetConsoleMode(hStdin, ctypes.byref(original_mode))
    kernel32.SetConsoleMode(hStdin, original_mode.value & ~0x0004) 
    
    sys.stdout.write("Microsoft Windows [Version 10.0.22631]\n(c) Microsoft Corporation. Tum haklari saklidir.\n\n[KAS HAFIZASI YEREL TEST MODU AKTIF]\nBir kelime yazin ve Enter'a basin...\n\nC:\\Users\\ortak>")
    sys.stdout.flush()
    
    module_handle = kernel32.GetModuleHandleW(None)
    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, pointer, module_handle, 0)
    
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        temizlik_yap()

if __name__ == "__main__":
    main()
