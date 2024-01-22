"""pgBackRest info JSON model derived directly from command output."""

# pylint: disable=missing-class-docstring,too-few-public-methods

from typing import Literal

from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import Field


class DatabaseShort(BaseModel):
    id: int
    repo_key: int = Field(alias="repo-key")


class Archive(BaseModel):
    database: DatabaseShort
    id: str
    max: str
    min: str


class BackupArchive(BaseModel):
    start: str
    stop: str


class Backrest(BaseModel):
    format: int
    version: str


class BackupInfoRepository(BaseModel):
    delta: int
    size: int


class BackupInfo(BaseModel):
    delta: int
    repository: BackupInfoRepository
    size: int


class Lsn(BaseModel):
    start: str
    stop: str


class Timestamp(BaseModel):
    start: int
    stop: int


class Backup(BaseModel):
    archive: BackupArchive
    backrest: Backrest
    database: DatabaseShort
    error: bool
    info: BackupInfo
    label: str
    lsn: Lsn
    prior: str | None
    reference: list[str] | None
    timestamp: Timestamp
    type: Literal["full", "diff", "incr"]


class DatabaseLong(BaseModel):
    id: int
    repo_key: int = Field(alias="repo-key")
    system_id: int = Field(alias="system-id")
    version: str


class RepositoryStatus(BaseModel):
    code: int
    message: str


class Repository(BaseModel):
    cipher: str
    key: int
    status: RepositoryStatus


class StatusLockBackup(BaseModel):
    held: bool


class StatusLock(BaseModel):
    backup: StatusLockBackup


class Status(BaseModel):
    code: int
    lock: StatusLock
    message: str


class PgBackRestInfo(BaseModel):
    archive: list[Archive]
    backup: list[Backup]
    cipher: str
    db: list[DatabaseLong]
    name: str
    repo: list[Repository]
    status: Status
