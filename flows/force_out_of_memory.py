"""
This script is used to force an out-of-memory error in a Prefect flow.

Use it to reproduce and diagnose memory issues.
"""

import os
from logging import Logger, LoggerAdapter

import psutil
from prefect import flow, get_run_logger

MEGABYTE: int = 10**6


def log_memory_usage(process: psutil.Process, logger: Logger | LoggerAdapter) -> None:
    mem_stats = psutil.virtual_memory()
    mem_process = process.memory_info().rss / MEGABYTE
    logger.info(
        f"[PID {os.getpid()}] process={mem_process} total={mem_stats.total / MEGABYTE} available={mem_stats.available / MEGABYTE} percent={mem_stats.percent} used={mem_stats.used / MEGABYTE} free={mem_stats.free / MEGABYTE}"
    )


@flow
def max_memory_usage():
    logger = get_run_logger()
    logger.warning("Starting max memory usage flow")

    process = psutil.Process(os.getpid())

    data = []
    while True:
        log_memory_usage(process, logger)
        try:
            data.append(bytearray(MEGABYTE))
        # MemoryError is not necessarily raised on all platforms
        # On Unix systems, the OOM killer generally terminate the process
        except MemoryError:
            logger.warning("Hit MemoryError!")
            break

    logger.warning("Completed max memory usage flow")


if __name__ == "__main__":
    max_memory_usage()
