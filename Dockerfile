ARG ALPINE_VERSION="3.19"
ARG PYTHON_VERSION="3.12"

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as base

# Upgrade to avoid CVE-2023-6237, CVE-2023-6129 (openssl) and CVE-2023-5752 (pip)
RUN apk add --no-cache --upgrade "libcrypto3>=3.1.4-r4" "libssl3>=3.1.4-r4" \
 && python3 -m pip install --no-cache-dir --progress-bar=off --root-user-action=ignore --upgrade "pip<=23.3"



FROM base as venv

COPY ./requirements.txt /tmp/requirements.txt

RUN apk add --no-cache gcc musl-dev \
 && python3 -m pip install --no-cache-dir --progress-bar=off --root-user-action=ignore pyclean

RUN python3 -m venv --without-pip /opt/venv \
 && python3 -m pip install \
        --no-cache-dir --progress-bar=off --root-user-action=ignore \
        --target $(find /opt/venv -name site-packages) -r /tmp/requirements.txt \
 \
 && python3 -m pyclean /opt/venv \
 && rm -v /tmp/requirements.txt



FROM base as pgbackrest_exporter

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY ./pgbackrest_exporter /opt/pgbackrest_exporter

RUN mkdir -v /docker-entrypoint.d/

COPY --from=venv /opt/venv /opt/venv

EXPOSE 8080
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD ["--help"]
