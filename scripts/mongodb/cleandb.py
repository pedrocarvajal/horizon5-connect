from multiprocessing import Process, Queue
from time import sleep
from typing import Any

from enums.db_command import DBCommand
from services.db import DBService
from services.logging import LoggingService


class DBManager(DBService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class DBCleaner:
    def __init__(
        self,
        db_commands_queue: Queue,
        db_events_queue: Queue,
    ) -> None:
        self._db_commands_queue = db_commands_queue
        self._db_events_queue = db_events_queue

        self._log = LoggingService()
        self._log.setup("cleandb")
        self._log.info("Database cleaner started")

        sleep(1)
        self._clean()

    def _clean(self) -> None:
        repositories = [
            "BacktestRepository",
            "SnapshotRepository",
            "OrderRepository",
        ]

        self._log.info(f"Repositories to clean: {len(repositories)}")

        for repository in repositories:
            self._db_delete_all(repository)
            self._log.info(f"{repository}: delete command sent")

        self._log.info("Database cleaned successfully")
        self._db_kill()

    def _db_delete_all(self, repository: str) -> None:
        self._db_commands_queue.put(
            {
                "command": DBCommand.DELETE,
                "repository": repository,
                "method": {
                    "name": "delete",
                    "arguments": {
                        "where": {},
                    },
                },
            }
        )

    def _db_kill(self) -> None:
        self._db_commands_queue.put(
            {
                "command": DBCommand.KILL,
            }
        )


if __name__ == "__main__":
    db_commands_queue = Queue()
    db_events_queue = Queue()

    processes = [
        Process(
            target=DBManager,
            kwargs={
                "db_commands_queue": db_commands_queue,
                "db_events_queue": db_events_queue,
            },
        ),
        Process(
            target=DBCleaner,
            kwargs={
                "db_commands_queue": db_commands_queue,
                "db_events_queue": db_events_queue,
            },
        ),
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()
