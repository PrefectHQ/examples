"""
This flow will log information about the current environment. Use it to
diagnose issues with your environment, especially when deploying to
infrastructure.
"""

import sys
import os
import platform
import socket

import httpx
import prefect


@prefect.flow
def whoami():
    logger = prefect.get_run_logger()

    data = {
        "Platform": platform.machine(),
        "OS": platform.version(),
        "Python": sys.version,
        "Prefect": prefect.__version__,
        "Hostname": socket.gethostname(),
        "Address": httpx.get("https://api.ipify.org").text,
        "User": os.getenv("USER"),
        "CWD": os.getcwd(),
        "CPUs": os.cpu_count(),
        "PID": os.getpid(),
        "UID": os.getuid(),
    }

    for key, value in data.items():
        logger.info(f"{key}: {value}")


if __name__ == "__main__":
    whoami()