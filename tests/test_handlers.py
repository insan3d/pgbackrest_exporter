"""Tests for HTTP handlers."""

from pathlib import Path
from typing import Iterable

import pytest

from aiohttp import ClientResponse
from aiohttp.test_utils import TestClient
from aiohttp.web import Application
from prometheus_client import Metric
from prometheus_client.parser import text_string_to_metric_families

from pgbackrest_exporter import __main__ as main


@pytest.mark.asyncio
async def test_landing(aiohttp_client: TestClient) -> None:
    """Test landing page."""

    app: Application = main.make_app(title="test", path="/metrics", commands_dict={})

    client = await aiohttp_client(app)  # type: ignore
    response: ClientResponse = await client.get(path="/")  # type: ignore
    assert response.status == 200  # type: ignore


@pytest.mark.asyncio
async def test_middlewares_metrics(aiohttp_client: TestClient) -> None:
    """Test internal metrics."""

    test_metrics_names = (
        "aiohttp_server_response_status",
        "aiohttp_server_respose_time",
        "exporter_collector_exceptions_total",
        "exporter_collector_stderr_lines_total",
        "pgbackrest_exporter_info",
    )
    test_metrics: dict[str, bool] = {name: False for name in test_metrics_names}

    app: Application = main.make_app(title="test", path="/metrics", commands_dict={})  # type: ignore
    client = await aiohttp_client(app)  # type: ignore
    response: ClientResponse = await client.get(path="/metrics")  # type: ignore
    metrics: Iterable[Metric] = text_string_to_metric_families(text=await response.text())  # type: ignore

    for metric in metrics:
        if metric.name in test_metrics_names:
            test_metrics[metric.name] = True

    assert all(test_metrics.values())


@pytest.mark.asyncio
async def test_pgbackrest_metrics(tmp_path: Path, aiohttp_client: TestClient) -> None:
    """Test metrics."""

    # pylint: disable=line-too-long
    test_input = r'[{"archive":[{"database":{"id":1,"repo-key":1},"id":"13-1","max":"00000001000000000000000B","min":"000000010000000000000003"}],"backup":[{"archive":{"start":"000000010000000000000005","stop":"000000010000000000000005"},"backrest":{"format":5,"version":"2.43"},"database":{"id":1,"repo-key":1},"error":false,"info":{"delta":24432739,"repository":{"delta":2986256,"size":2986256},"size":24432739},"label":"20240119-062014F","lsn":{"start":"0/5000028","stop":"0/5000138"},"prior":null,"reference":null,"timestamp":{"start":1705634414,"stop":1705634422},"type":"full"},{"archive":{"start":"000000010000000000000007","stop":"000000010000000000000007"},"backrest":{"format":5,"version":"2.43"},"database":{"id":1,"repo-key":1},"error":false,"info":{"delta":9902,"repository":{"delta":925,"size":2986259},"size":24433039},"label":"20240119-062014F_20240119-064905D","lsn":{"start":"0/7000028","stop":"0/7000100"},"prior":"20240119-062014F","reference":["20240119-062014F"],"timestamp":{"start":1705636145,"stop":1705636147},"type":"diff"},{"archive":{"start":"000000010000000000000009","stop":"000000010000000000000009"},"backrest":{"format":5,"version":"2.43"},"database":{"id":1,"repo-key":1},"error":false,"info":{"delta":10202,"repository":{"delta":928,"size":2986262},"size":24433339},"label":"20240119-062014F_20240119-064924I","lsn":{"start":"0/9000028","stop":"0/9000100"},"prior":"20240119-062014F_20240119-064905D","reference":["20240119-062014F","20240119-062014F_20240119-064905D"],"timestamp":{"start":1705636164,"stop":1705636166},"type":"incr"},{"archive":{"start":"00000001000000000000000B","stop":"00000001000000000000000B"},"backrest":{"format":5,"version":"2.43"},"database":{"id":1,"repo-key":1},"error":false,"info":{"delta":10528,"repository":{"delta":972,"size":2986262},"size":24433639},"label":"20240119-062014F_20240120-040002D","lsn":{"start":"0/B000028","stop":"0/B000100"},"prior":"20240119-062014F","reference":["20240119-062014F"],"timestamp":{"start":1705712402,"stop":1705712404},"type":"diff"}],"cipher":"none","db":[{"id":1,"repo-key":1,"system-id":7322494622595299123,"version":"13"}],"name":"tsoo-app","repo":[{"cipher":"none","key":1,"status":{"code":0,"message":"ok"}}],"status":{"code":0,"lock":{"backup":{"held":false}},"message":"ok"}}]'

    test_metrics_names = (
        "pgbackrest_common_status",
        "pgbackrest_repository_status",
        "pgbackrest_backup_status",
        "pgbackrest_backup_last_start_time",
        "pgbackrest_backup_duration",
        "pgbackrest_backup_delta",
        "pgbackrest_backup_size",
    )
    test_metrics: dict[str, bool] = {name: False for name in test_metrics_names}

    tempfile: Path = tmp_path / "test"
    with open(file=tempfile, mode="w", encoding="utf-8") as writer:
        writer.write(test_input)

    app: Application = main.make_app(
        title="test", path="/metrics", commands_dict={"test": f"cat {tempfile}"}
    )

    client = await aiohttp_client(app)  # type: ignore
    response: ClientResponse = await client.get(path="/metrics")  # type: ignore
    metrics: Iterable[Metric] = text_string_to_metric_families(text=await response.text())  # type: ignore

    for metric in metrics:
        if metric.name in test_metrics_names:
            test_metrics[metric.name] = True

    assert all(test_metrics.values())
