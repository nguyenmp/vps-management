# https://community.n8n.io/t/the-definitive-guide-to-custom-npm-modules-for-self-hosted-instances/50948

FROM n8nio/n8n:latest
USER root

RUN echo "Installing custom npm packages for n8n"
RUN npm install -g moment lodash instagram-private-api
ENV NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash,instagram-private-api

# https://stackoverflow.com/questions/62554991/how-do-i-install-python-on-alpine-linux
RUN echo "Installing python3"
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python

USER node
RUN echo "Creating venv for user (not root) so that I can pip install from n8n"
RUN python3 -m venv /home/node/venv
ENV PATH="/home/node/venv/bin:$PATH"
RUN python3 -m ensurepip
RUN pip install --upgrade pip

RUN echo "Installing yt-dlp"
RUN pip install yt-dlp

