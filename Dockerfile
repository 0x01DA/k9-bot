FROM python:3.8-slim

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        libmagic1 \
        build-essential \
        git

RUN git clone --depth 1 https://gitlab.matrix.org/matrix-org/olm.git /tmp/libolm \
    && cd /tmp/libolm \
    && make install

WORKDIR /bot

COPY requirements.txt dpkg_requirements.txt aliases.yaml /bot/

RUN pip install -r requirements.txt
RUN apt-get install -y $(head -n1 dpkg_requirements.txt)

RUN apt-get purge -y build-essential && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY scripts /bot/scripts/
COPY *.py /bot/

CMD [ "python", "./main.py" ]
