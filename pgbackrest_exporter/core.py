"""Metrics fetcher and updater for single target."""

from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE, Process
from json import loads
from logging import Logger, getLogger
from typing import Any, Literal

from prometheus_client import Counter, Gauge

from pgbackrest_exporter.models import PgBackRestInfo

logger: Logger = getLogger(name=__name__)

EXCEPTIONS_METRIC = Counter(
    namespace="exporter",
    subsystem="collector",
    name="exceptions",
    documentation="Count of exceptions during collecting and exporting metrics",
    labelnames=("target",),
)

STDERR_METRIC = Counter(
    namespace="exporter",
    subsystem="collector",
    name="stderr_lines",
    documentation="Count of STDERR lines captured during collecting and exporting metrics",
    labelnames=("target",),
)

PGBACKREST_COMMON_STATUS = Gauge(
    namespace="pgbackrest",
    subsystem="common",
    name="status",
    documentation="Current pgBackRest status",
    labelnames=("command", "name"),
)

PGBACKREST_REPO_STATUS = Gauge(
    namespace="pgbackrest",
    subsystem="repository",
    name="status",
    documentation="Current repository status",
    labelnames=("command", "stanza", "repo"),
)

PGBACKREST_BACKUP_STATUS = Gauge(
    namespace="pgbackrest",
    subsystem="backup",
    name="status",
    documentation="Current backup status",
    labelnames=("command", "stanza", "database", "repo", "backup_type"),
)

PGBACKREST_BACKUP_START = Gauge(
    namespace="pgbackrest",
    subsystem="backup",
    name="last_start_time",
    documentation="Backup last start time",
    labelnames=("command", "stanza", "database", "repo", "backup_type"),
)

PGBACKREST_BACKUP_DURATION = Gauge(
    namespace="pgbackrest",
    subsystem="backup",
    name="duration",
    documentation="Last backup duration",
    labelnames=("command", "stanza", "database", "repo", "backup_type"),
)

PGBACKREST_BACKUP_DELTA = Gauge(
    namespace="pgbackrest",
    subsystem="backup",
    name="delta",
    documentation="Backup delta size",
    labelnames=("command", "stanza", "database", "repo", "backup_type", "compressed"),
)

PGBACKREST_BACKUP_SIZE = Gauge(
    namespace="pgbackrest",
    subsystem="backup",
    name="size",
    documentation="Actual backup size",
    labelnames=("command", "stanza", "database", "repo", "backup_type", "compressed"),
)


async def update_target(target: str, command: str) -> tuple[str, int]:
    """Execute single command and update metrics."""
    try:
        # Execute command asynchronously
        logger.info("Target: %s, executing command: %s", target, command)
        process: Process = await create_subprocess_shell(cmd=command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = await process.communicate()

        # Print command's stderr to log
        if stderr:
            for line in stderr.decode(encoding="utf-8").splitlines():
                STDERR_METRIC.labels(target).inc()
                logger.error("Target %s produced stderr: %s", target, line)

        # Fail if no output produced
        if not stdout:
            EXCEPTIONS_METRIC.labels(target).inc()
            logger.error("Target %s produced no stdout", target)
            return target, -1

        # Output is JSON array
        output: list[dict[str, Any]] = loads(s=stdout.decode(encoding="utf-8"))
        for result in output:
            # Parse and validate JSON using model
            parsed = PgBackRestInfo(**result)
            target_labelvalues: tuple[str, str] = target, parsed.name

            # Update common status metric
            PGBACKREST_COMMON_STATUS.labels(*target_labelvalues).set(value=parsed.status.code)

            # Update repos status metric
            for repo in parsed.repo:
                PGBACKREST_REPO_STATUS.labels(*target_labelvalues, repo.key).set(
                    value=repo.status.code
                )

            # Update backup metrics
            for backup in parsed.backup:
                common_labelvalues: tuple[str, str, int, int, Literal["full", "diff", "incr"]] = (
                    *target_labelvalues,
                    backup.database.id,
                    backup.database.repo_key,
                    backup.type,
                )

                # Update status metric
                PGBACKREST_BACKUP_STATUS.labels(*common_labelvalues).set(value=int(backup.error))

                # Update last start time and duration metrics
                backup_start_time: int = backup.timestamp.start
                PGBACKREST_BACKUP_START.labels(*common_labelvalues).set(value=backup_start_time)
                PGBACKREST_BACKUP_DURATION.labels(*common_labelvalues).set(
                    value=backup.timestamp.stop - backup_start_time
                )

                # Update size metrics
                PGBACKREST_BACKUP_DELTA.labels(*common_labelvalues, "no").set(
                    value=backup.info.delta
                )
                PGBACKREST_BACKUP_DELTA.labels(*common_labelvalues, "yes").set(
                    value=backup.info.repository.delta
                )
                PGBACKREST_BACKUP_SIZE.labels(*common_labelvalues, "no").set(value=backup.info.size)
                PGBACKREST_BACKUP_SIZE.labels(*common_labelvalues, "yes").set(
                    value=backup.info.repository.size
                )

    # Count all exceptions and don't let collector to fail
    except Exception as exc:  # pylint: disable=broad-exception-caught
        EXCEPTIONS_METRIC.labels(target).inc()
        logger.exception(msg=exc)
        return target, -1

    return target, process.returncode if process.returncode else -1
