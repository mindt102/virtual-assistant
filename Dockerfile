FROM python:3.11-bookworm

# WORKDIR /usr/src/app

RUN apt update -y
RUN apt install autossh
COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

ARG PUID 
ARG PGID
ARG USER

RUN groupadd -g ${PGID} ${USER} && useradd -m -u ${PUID} -g ${PGID} ${USER} -s /bin/sh && su ${USER}

COPY . .
RUN chmod +x ./launch.sh

# If launch.sh does not exists, use CMD python3 ./main.py
CMD ./launch.sh 
