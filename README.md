# pgBackRest metrics exporter

## Overview

`pgbackrest_exporter` parses informational JSON received in standard output of provided commands and converts it into Prometheus-compatible (`application/openmetrics-text`) format served on specified port and path (`0.0.0.0:8080/metrics` by default).

## Usage

Commandline flags:

- `-h`, `--help`: show help message and exit
- `--version`: show program's version number and exit
- `-V`, `--verbose`: produce verbose output
- `-H`, `--host`: specify host to bind to (default: 0.0.0.0)
- `-P`, `--port`: specify port to bind to (default: 8080)
- `-U`, `--path`: specify path to serve metrics on (default: /metrics)
- `-c`, `--command`: name of command and command to execute
- `-f`, `--file`: name of command and file with command to execute

Commands may be repeaded as many times as needed and will be executed concurrenly when metrics endpoint requested. Commands or files should be specified as `key`=`value` pair, e.g.:

```bash session
pgbackrest_exporter --command test="sshpass -p "${TEST_PASSWORD}" ssh -o StrictHostKeyChecking=no root@"${TEST_HOST}" sudo -u postgres pgbackrest info --output=json"
```

So when requested for metrics, for "target" `test` `pgbackrest_exporter` will execute command `sshpass -p "${TEST_PASSWORD}" ssh -o StrictHostKeyChecking=no root@"${TEST_HOST}" sudo -u postgres pgbackrest info --output=json`.

## Distribution

`pgbackrest_exporter` provides two ways to distribute itself: as PyInstaller binary file and as Docker image.

### Running in Docker

As base image of Alpine Linux does not contain SSH client, if it is needed, it should be installed when running container. For this, you can use `/docker-entrypoint.d` directory, where each file will be executed before running exporter itself. For example:

`/docker-entrypoint.d/00_install-ssh.sh`
```bash
#!/usr/bin/env ash
# shellcheck shell=dash

apk add --no-cache sshpass openssh-client
```

So `docker run` command may look like something like that:

```bash session
docker run --detach --name pgbackrest_exporter -p 8080:8080/tcp \
    -v ./00_install-ssh.sh:/docker-entrypoint.d/00_install-ssh.sh \
    -e TEST_PASSWORD=r00t -e TEST_HOST=docker.host.internal \
    pgbackrest_exporter:0.1.0-development \
    --command test="sshpass -p "${TEST_PASSWORD}" ssh -o StrictHostKeyChecking=no root@"${TEST_HOST}" sudo -u postgres pgbackrest info --output=json"
```

## Provided metrics

### Main metrics

Metrics what are extracted from informational JSON are:

| Name                                | Type  | Labels                                                               | Description               |
|-------------------------------------|-------|----------------------------------------------------------------------|---------------------------|
| `pgbackrest_common_status`          | Gauge | `command`, `name`                                                    | Current pgBackRest status |
| `pgbackrest_repository_status`      | Gauge | `command`, `repo`, `stanza`                                          | Current repository status |
| `pgbackrest_backup_status`          | Gauge | `command`, `stanza`, `database`, `repo`, `backup_type`               | Current backup status     |
| `pgbackrest_backup_last_start_time` | Gauge | `command`, `stanza`, `database`, `repo`, `backup_type`               | Backup last start time    |
| `pgbackrest_backup_duration`        | Gauge | `command`, `stanza`, `database`, `repo`, `backup_type`               | Last backup duration      |
| `pgbackrest_backup_delta`           | Gauge | `command`, `stanza`, `database`, `repo`, `backup_type`, `compressed` | Backup delta size         |
| `pgbackrest_backup_size`            | Gauge | `command`, `stanza`, `database`, `repo`, `backup_type`, `compressed` | Actual backup size        |

Labels are:

- `command`: name of command passed with `--command` or `--file` commandline argument
- `name`: parsed stanza configuration name
- `repo`: parsed ID of repository (integer value)
- `stanza`: parsed stanza name fom backup or repository information section
- `database`: parsed ID of database (integer value)
- `backup_type`: one of `full`, `diff` or `incr`
- `compressed`: one of `yes` or `no` for exporting actual on-disk size and compressed size in repository

### Exporter metrics

`pgbackrest_exporter` provides own internal metrics for convinience:

| Name                                    | Type      | Labels                                              | Description                                                            |
|-----------------------------------------|-----------|-----------------------------------------------------|------------------------------------------------------------------------|
| `exporter_collector_exceptions_total`   | Counter   | `target`                                            | Count of exceptions during collecting and exporting metrics            |
| `exporter_collector_stderr_lines_total` | Counter   | `target`                                            | Count of STDERR lines captured during collecting and exporting metrics |
| `aiohttp_server_respose_time`           | Histogram | `path`                                              | HTTP request handler execution time                                    |
| `aiohttp_server_response_status_total`  | Counter   | `path`                                              | HTTP responses code count                                              |
| `pgbackrest_exporter_info`              | Gauge     | `major`, `minor`, `patchlevel`, `status`, `version` | `pgbackrest_exporter` information                                      |

### Python metrics

Default `prometheus_client` metrics are:

| Name                                    | Type    | Labels       | Description                                                                                          |
|-----------------------------------------|---------|--------------|------------------------------------------------------------------------------------------------------|
| `python_gc_objects_collected_total`     | Counter | `generation`                                                | Objects collected during GC                           |
| `python_gc_objects_uncollectable_total` | Counter | `generation`                                                | Uncollectable objects found during GC                 |
| `python_gc_collections_tota`            | Counter | `generation`                                                | Number of times this generation was                   |
| `python_info`                           | Gauge   | `implementation`, `major`, `minor`, `patchlevel`, `version` | Python platform information                           |
| `process_virtual_memory_bytes`          | Gauge   |                                                             | Virtual memory size in bytes                          |
| `process_resident_memory_bytes`         | Gauge   |                                                             | Resident memory size in bytes                         |
| `process_start_time_seconds`            | Gauge   |                                                             | Start time of the process since unix epoch in seconds |
| `process_cpu_seconds_total`             | Gauge   |                                                             | Total user and system CPU time spent in seconds       |
| `process_open_fds`                      | Gauge   |                                                             | Number of open file descriptors                       |
| `process_max_fds`                       | Gauge   |                                                             | Maximum number of open file descriptors               |


## Building

Everything needed to re-build `pgbackrest_exporter` is located in `Makefile`. Targets are:

- `venv`: setup fresh Python environment
- `link`: lint code with PyLint
- `test`: test code with PyTest
- `image`: build Docker image
- `binary`: build PyInstaller binary
- `clean`: cleanup everything

Default target is to build PyInstaller binary.
