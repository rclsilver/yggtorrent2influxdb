ARG PLATFORM
ARG QEMU_BIN

FROM ${PLATFORM}/python:3.7-alpine

COPY ${QEMU_BIN} /usr/bin/

ENV VERSION 1.0.0

COPY yggtorrent2influxdb.py /usr/local/bin/yggtorrent2influxdb
COPY requirements.txt /tmp/requirements.txt

RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

CMD [ "python", "/usr/local/bin/yggtorrent2influxdb" ]
