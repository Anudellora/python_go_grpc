#!/usr/bin/env python3
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

os.chdir(Path(__file__).resolve().parent.parent)
Path("artifacts").mkdir(exist_ok=True)
if not Path("certs/server.pem").exists():
    subprocess.run(["sh", "certs.sh"], check=True)
subprocess.run(["nginx", "-t", "-p", str(Path.cwd())+"/", "-c", "nginx.conf"], check=True)
subprocess.run([sys.executable, "manage.py", "check"], check=True)
commands = {
    "go-server": ["./bin/dice-server"],
    "nginx": ["nginx", "-p", str(Path.cwd())+"/", "-c", "nginx.conf", "-g", "daemon off;"],
    "django-8000": [sys.executable, "manage.py", "runserver", "0.0.0.0:8000", "--noreload"],
    "django-8001": [sys.executable, "manage.py", "runserver", "0.0.0.0:8001", "--noreload"],
}
processes=[]
files=[]
def stop(signum=None, frame=None):
    for proc in processes:
        if proc.poll() is None: proc.terminate()
signal.signal(signal.SIGTERM,stop)
signal.signal(signal.SIGINT,stop)
try:
    for name,command in commands.items():
        output=open(f"artifacts/{name}.log","a",buffering=1)
        files.append(output)
        processes.append(subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT))
        print(f"STARTED {name}",flush=True)
    while all(proc.poll() is None for proc in processes):
        time.sleep(0.5)
finally:
    stop()
    for proc in processes:
        try: proc.wait(timeout=8)
        except subprocess.TimeoutExpired: proc.kill();proc.wait()
    for output in files: output.close()
