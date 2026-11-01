# https://community.n8n.io/t/the-definitive-guide-to-custom-npm-modules-for-self-hosted-instances/50948

FROM n8nio/n8n:latest
USER root

RUN echo "Installing custom npm packages for n8n"
RUN npm install -g moment lodash instagram-private-api jsdom md5
ENV NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash,instagram-private-api,jsdom,md5

# https://stackoverflow.com/questions/62554991/how-do-i-install-python-on-alpine-linux
RUN echo "Installing python3"
RUN . /etc/os-release && \
    alpine_ver=$(echo "$VERSION_ID" | cut -d'.' -f1,2) && \
    echo "Detected Alpine v${alpine_ver}" && \
    apk_name=$(wget -q "https://dl-cdn.alpinelinux.org/alpine/v${alpine_ver}/main/$(uname -m)/" -O - | \
               grep apk-tools-static | cut -d '"' -f2) && \
    wget -q "https://dl-cdn.alpinelinux.org/alpine/v${alpine_ver}/main/$(uname -m)/$apk_name" && \
    tar -xzf $apk_name -C / && \
    rm $apk_name
RUN /sbin/apk.static add --upgrade apk-tools libapk2
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python

RUN echo "Installing ffmpeg (for yt-dlp)"
RUN apk add --update --no-cache ffmpeg

RUN echo "Installing deno (for yt-dlp)"
RUN curl -fsSL https://deno.land/install.sh | sh

RUN echo "Installing aws-cli"
# dhi.io serves docutils files that no longer match its own index, so apk
# rejects them with "v2 package integrity error". Reported 2026-11-01 to the
# Docker Community Forum, pending moderation, under the title:
#   dhi.io serves an old py3.14-docutils, so apk add fails with "v2 package
#   integrity error"
# https://forums.docker.com/u/markerz/activity/pending
# Until that mirror is fixed, drop it here and take the packages from the
# official Alpine CDN. Cost: aws-cli 2.34.63-r0 instead of 2.35.15-r1.
RUN sed -i '/dhi\.io/d' /etc/apk/repositories && \
    apk add --update --no-cache aws-cli

USER node
RUN echo "Creating venv for user (not root) so that I can pip install from n8n"
RUN python3 -m venv /home/node/venv
ENV PATH="/home/node/venv/bin:$PATH"
RUN python3 -m ensurepip
RUN pip install --upgrade pip

RUN echo "Installing yt-dlp"
RUN pip install "yt-dlp[default]"
