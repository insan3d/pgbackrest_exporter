"""`aiohttp` server handlers and metrics middlewares."""

from asyncio import Task, create_task, gather
from time import time

from aiohttp.typedefs import Handler
from aiohttp.web import Request, Response, StreamResponse, middleware
from prometheus_client import Counter, Histogram, generate_latest

from pgbackrest_exporter.core import update_target

_LANDING = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
    </head>
    <body>
        <p>Looking for <a href="{metrics_path}">{metrics_path}</a>?</p>
    </body>
</html>
"""

RESPONSE_TIME_METRIC = Histogram(
    namespace="aiohttp",
    subsystem="server",
    name="respose_time",
    documentation="HTTP request handler execution time",
    labelnames=("path",),
)

RESPONSE_STATUS_METRIC = Counter(
    namespace="aiohttp",
    subsystem="server",
    name="response_status",
    documentation="HTTP responses code count",
    labelnames=("path", "status"),
)


@middleware
async def timed_mw(request: Request, handler: Handler) -> StreamResponse:
    """Observe handler execution time into Prometheus metric."""

    start: float = time()
    response: StreamResponse = await handler(request)
    spent: float = time() - start

    RESPONSE_TIME_METRIC.labels(request.path).observe(amount=spent)
    return response


@middleware
async def status_mw(request: Request, handler: Handler) -> StreamResponse:
    """Count returned HTTP codes into Prometheus metric."""

    response: StreamResponse = await handler(request)
    RESPONSE_STATUS_METRIC.labels(request.path, response.status).inc()
    return response


async def serve_landing(request: Request) -> Response:
    """Serve landing page."""

    content: str = _LANDING.format(
        title=request.app["insan3d.pgbackrest_exporter.html.title"],
        metrics_path=request.app["insan3d.pgbackrest_exporter.html.metrics_path"],
    )

    return Response(body=content, content_type="text/html")


async def serve_metrics(request: Request) -> Response:
    """Serve metrics page."""

    tasks: list[Task[tuple[str, int]]] = []
    for target, command in request.app["instan3d.pgbackrest_exporter.commands"].items():
        tasks.append(create_task(coro=update_target(target=target, command=command)))

    await gather(*tasks)

    content: bytes = generate_latest()
    return Response(body=content, content_type="text/plain")
