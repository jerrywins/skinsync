"""RQ worker entry point: `python -m skinsync.worker`. Also schedules hourly retention cleanup."""

import logging
import threading
import time

from rq import Queue, Worker

from .jobs import retention_cleanup
from .observability import setup_logging
from .security import get_redis


def _retention_loop() -> None:
    while True:
        try:
            retention_cleanup()
        except Exception:
            logging.getLogger("skinsync.worker").exception("retention cleanup failed")
        time.sleep(3600)


def main() -> None:
    setup_logging()
    threading.Thread(target=_retention_loop, daemon=True).start()
    q = Queue("skinsync", connection=get_redis())
    Worker([q], connection=get_redis()).work(with_scheduler=True)


if __name__ == "__main__":
    main()
