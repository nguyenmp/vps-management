# https://community.n8n.io/t/the-definitive-guide-to-custom-npm-modules-for-self-hosted-instances/50948

FROM n8nio/n8n:latest
USER root

RUN echo "Installing custom npm packages for n8n"
RUN npm install -g moment lodash instagram-private-api jsdom md5
ENV NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash,instagram-private-api,jsdom,md5

# https://stackoverflow.com/questions/62554991/how-do-i-install-python-on-alpine-linux
RUN echo "Installing python3"
RUN wget https://dl-cdn.alpinelinux.org/alpine/v3.23/main/$(uname -m)/apk-tools-static-3.0.3-r1.apk
RUN tar -xzf apk-tools-static-3.0.3-r1.apk -C /
RUN /sbin/apk.static add apk-tools
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python

RUN echo "Installing ffmpeg (for yt-dlp)"
RUN apk add --update --no-cache ffmpeg

RUN echo "Installing deno (for yt-dlp)"
RUN curl -fsSL https://deno.land/install.sh | sh

RUN echo "Installing aws-cli"
RUN apk add --update --no-cache aws-cli

USER node
RUN echo "Creating venv for user (not root) so that I can pip install from n8n"
RUN python3 -m venv /home/node/venv
ENV PATH="/home/node/venv/bin:$PATH"
RUN python3 -m ensurepip
RUN pip install --upgrade pip

RUN echo "Installing yt-dlp"
RUN pip install "yt-dlp[default]"

