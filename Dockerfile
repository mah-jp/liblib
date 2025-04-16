# syntax=docker/dockerfile:1

# Docker | Playwright Python > Build your own image
# https://playwright.dev/python/docs/docker#build-your-own-image
FROM python:3.12-bookworm

# for playwright
RUN apt-get update && apt-get install -y \
	libasound2 \
	libatk-bridge2.0-0 \
	libatk1.0-0 \
	libatspi2.0-0 \
	libcups2 \
	libdbus-1-3 \
	libdrm2 \
	libgbm1 \
	libnspr4 \
	libnss3 \
	libxcomposite1 \
	libxdamage1 \
	libxfixes3 \
	libxkbcommon0 \
	libxrandr2

RUN pip install playwright && \
	playwright install chromium

# for etc
RUN apt-get install -y \
	jq \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

ENV DIR_ME='/opt/liblib'
ENV DIR_DOCKER='./docker'
ENV LANG='ja_JP.UTF-8'
ENV TZ='Asia/Tokyo'
WORKDIR $DIR_ME

# for liblib
COPY $DIR_DOCKER/requirements.txt .
RUN pip install -r requirements.txt
COPY $DIR_DOCKER/book2json_d-library.py .
RUN chmod +x book2json_d-library.py
COPY $DIR_DOCKER/book2json_opac.py .
RUN chmod +x book2json_opac.py
COPY $DIR_DOCKER/book2json_wrapper.sh .
RUN chmod +x book2json_wrapper.sh
COPY $DIR_DOCKER/json2message.py .
RUN chmod +x json2message.py

ENTRYPOINT ["/bin/bash"]
CMD ["-c", "$DIR_ME/book2json_wrapper.sh"]
