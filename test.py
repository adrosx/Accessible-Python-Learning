import psutil
import os
print(f"PID mojego procesu: {os.getpid()}")
for proc in psutil.process_iter(['pid', 'name']):
    print(proc.info)