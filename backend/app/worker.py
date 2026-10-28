"""Proceso de trabajos de video, separado del servidor HTTP.

Uso: python -m app.worker  (Ctrl+C para detener)
"""
import signal
import time

from .db import SessionLocal
from .services.jobs import run_once, WORKER_ID

_stop = False


def _handle(*_):
    global _stop
    _stop = True


def main(poll_seconds: float = 2.0):
    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)
    print(f"Worker Kinetra {WORKER_ID} iniciado")
    while not _stop:
        with SessionLocal() as db:
            worked = run_once(db)
        if not worked:
            time.sleep(poll_seconds)
    print("Worker detenido")


if __name__ == "__main__":
    main()
