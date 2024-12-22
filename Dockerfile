FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

USER root

ARG DEBIAN_FRONTEND=noninteractive

LABEL github_repo="https://github.com/hordechief/F5-TTS"

RUN set -x \
    && apt-get update \
    && apt-get -y install wget curl man git less openssl libssl-dev unzip unar build-essential aria2 tmux vim \
    && apt-get install -y openssh-server sox libsox-fmt-all libsox-fmt-mp3 libsndfile1-dev ffmpeg \
    && apt-get install -y librdmacm1 libibumad3 librdmacm-dev libibverbs1 libibverbs-dev ibverbs-utils ibverbs-providers \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
    
WORKDIR /workspace
# ENV http_proxy=http://172.17.0.1:7897/
# ENV https_proxy=http://172.17.0.1:7897/
# ENV socks5_proxy=172.17.0.1:7897/
# ENV no_proxy="localhost,127.0.0.1"
ENV DATA_DIR="/home/aurora/data"
ENV OUTPUT_DIR="/home/aurora/output"
ENV PORT=8890

RUN git clone https://github.com/hordechief/F5-TTS.git \
    && cd F5-TTS \
    && git submodule update --init --recursive \
    && sed -i '7iimport sys\nsys.path.append(os.path.dirname(os.path.abspath(__file__)))' src/third_party/BigVGAN/bigvgan.py \
    && pip install -e . --no-cache-dir

RUN pip install flask

ENV SHELL=/bin/bash

WORKDIR /workspace/F5-TTS
