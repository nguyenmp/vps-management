# https://community.n8n.io/t/the-definitive-guide-to-custom-npm-modules-for-self-hosted-instances/50948

FROM n8nio/n8n:latest
USER root
RUN npm install -g moment lodash instagram-private-api
ENV NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash,instagram-private-api
USER node
