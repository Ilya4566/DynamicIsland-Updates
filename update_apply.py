# -*- coding: utf-8 -*-
"""Applies a downloaded DynamicIsland update, logs errors and relaunches the app."""
import os, sys, time, zipfile, shutil, subprocess, tempfile, traceback


def log(folder, message):
    try:
        with open(os.path.join(folder, "update_install.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(message) + "\n")
    except Exception:
        pass


def wait_for_pid(pid, timeout=120):
    if os.name != "nt":
        deadline = time.time() + timeout
        while time.time() < deadline:
            try: os.kill(pid, 0)
            except OSError: return
            time.sleep(.25)
        raise TimeoutError("Приложение не завершилось за отведённое время")
    import ctypes
    from ctypes import wintypes
    SYNCHRONIZE = 0x00100000
    WAIT_OBJECT_0 = 0x00000000
    WAIT_TIMEOUT = 0x00000102
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
    if not handle:
        # The app may already have exited before the updater starts.
        return
    try:
        result = kernel32.WaitForSingleObject(handle, int(timeout * 1000))
        if result == WAIT_TIMEOUT:
            raise TimeoutError("DynamicIsland не закрылся за 120 секунд")
        if result != WAIT_OBJECT_0:
            raise OSError(ctypes.get_last_error(), "Не удалось дождаться закрытия приложения")
    finally:
        kernel32.CloseHandle(handle)


def main():
    if len(sys.argv) < 4: return 2
    pid, archive, app_path = int(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
    folder = os.path.dirname(app_path)
    allowed = {"island.pyw", "core.py", "update_client.py", "update_apply.py"}
    backup = os.path.join(folder, "update_backup", time.strftime("%Y%m%d_%H%M%S"))
    stage = tempfile.mkdtemp(prefix="di_update_stage_", dir=folder)
    try:
        log(folder, f"Старт установки: pid={pid}, archive={archive}")
        wait_for_pid(pid)
        os.makedirs(backup, exist_ok=True)
        with zipfile.ZipFile(archive, "r") as zf:
            for info in zf.infolist():
                name = os.path.basename(info.filename)
                if name not in allowed or info.is_dir(): continue
                dest = os.path.join(stage, name)
                with zf.open(info) as src, open(dest, "wb") as out: shutil.copyfileobj(src, out)
        missing = [n for n in allowed if not os.path.isfile(os.path.join(stage, n))]
        if missing: raise RuntimeError("В архиве отсутствуют: " + ", ".join(sorted(missing)))
        for name in allowed:
            target = os.path.join(folder, name)
            if os.path.exists(target): shutil.copy2(target, os.path.join(backup, name))
            shutil.copy2(os.path.join(stage, name), target)
        log(folder, "Файлы обновлены, перезапускаю приложение")
        subprocess.Popen([sys.executable, app_path], cwd=folder,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return 0
    except Exception:
        log(folder, "ОШИБКА УСТАНОВКИ\n" + traceback.format_exc())
        for name in allowed:
            old = os.path.join(backup, name)
            if os.path.isfile(old):
                try: shutil.copy2(old, os.path.join(folder, name))
                except Exception: log(folder, "Ошибка отката: " + name + "\n" + traceback.format_exc())
        try: subprocess.Popen([sys.executable, app_path], cwd=folder)
        except Exception: log(folder, "Не удалось перезапустить приложение\n" + traceback.format_exc())
        return 1
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        try: os.remove(archive)
        except OSError: pass


if __name__ == "__main__":
    raise SystemExit(main())
