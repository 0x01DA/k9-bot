FROM python:3-slim

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        libmagic1 \
        build-essential \
        git cmake

RUN git clone --depth 1 https://gitlab.matrix.org/matrix-org/olm.git /tmp/libolm \
    && cd /tmp/libolm \
    && cmake . -Bbuild \
	 && cmake --build build \
	 && cmake --install build

RUN pip install -U wheel pip && \
    cd /tmp/libolm/python && make headers && make install && \
    pip install . && mkdir /bot && cd /bot

COPY requirements.txt dpkg_requirements.txt aliases.yaml /bot/
RUN apt-get install -y $(head -n1 /bot/dpkg_requirements.txt)
RUN pip install -r /bot/requirements.txt

RUN apt-get purge -y build-essential && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /bot
COPY scripts /bot/scripts/
ENV PATH="${PATH}:/bot/scripts"
COPY *.py /bot/

CMD [ "python3", "/bot/main.py" ]

