# syntax=docker/dockerfile:1

# Dockerfile for liblib (Ver.20260331)

FROM python:3.13-slim-trixie

ENV DIR_ME='/opt/liblib' \
	DIR_DOCKER='./docker' \
	LANG='ja_JP.UTF-8' \
	TZ='Asia/Tokyo'

WORKDIR $DIR_ME

# Install system dependencies
RUN apt-get update && apt-get install -y \
	jq \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies and patchright browsers
COPY $DIR_DOCKER/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
	&& patchright install-deps \
	&& patchright install chromium \
	&& rm -rf /var/lib/apt/lists/*

# Copy scripts and set permissions
COPY --chmod=755 $DIR_DOCKER/book2json_d-library.py \
	$DIR_DOCKER/book2json_opac.py \
	$DIR_DOCKER/book2json_wrapper.sh \
	$DIR_DOCKER/json2message.py \
	./

ENTRYPOINT ["/bin/bash"]
CMD ["-c", "$DIR_ME/book2json_wrapper.sh"]
