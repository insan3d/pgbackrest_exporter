#!/usr/bin/env ash
# shellcheck shell=dash

chmod -v +x /docker-entrypoint.d/*
run-parts /docker-entrypoint.d/
/opt/venv/bin/python3 /opt/pgbackrest_exporter "$@"
