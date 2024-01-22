FROM python:alpine as venv

COPY ./requirements.txt /tmp/requirements.txt

RUN apk add --no-cache gcc musl-dev \
 && python3 -m pip install --no-cache-dir --progress-bar=off --root-user-action=ignore \
        --upgrade pip pyclean setuptools wheel

RUN python3 -m venv --without-pip /opt/venv \
 && python3 -m pip install \
        --no-cache-dir --progress-bar=off --root-user-action=ignore \
        --target $(find /opt/venv -name site-packages) -r /tmp/requirements.txt \
 \
 && python3 -m pyclean /opt/venv \
 && rm -v /tmp/requirements.txt



FROM python:alpine

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY ./pgbackrest_exporter /opt/pgbackrest_exporter

RUN mkdir -v /docker-entrypoint.d/

COPY --from=venv /opt/venv /opt/venv

EXPOSE 8080
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD ["--help"]
