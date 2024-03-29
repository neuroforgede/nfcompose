# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

FROM nginx:1.23.3
RUN apt-get update && apt-get upgrade -y

# update the image
RUN apt-get update -y && apt-get upgrade -y

# to have a sane default, but in production this should be mounted outside so that it is updated regularly
RUN mkdir -p /neuroforge/skipper/
RUN cp /etc/ssl/certs/ca-certificates.crt /neuroforge/skipper/trusted_ca.crt
RUN rm /etc/nginx/conf.d/default.conf

COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./conf.d/default.conf /neuroforge/skipper/default.conf

ENV SKIPPER_BACKEND_SERVICE=skipper.local
ENV SKIPPER_BACKEND_SERVICE_PORT=8000
ENV SKIPPER_DNS_RESOLVER_VALID=10s
ENV HEALTH_ENDPOINT=/healthz/

CMD envsubst '$HEALTH_ENDPOINT, $SKIPPER_BACKEND_SERVICE, $SKIPPER_BACKEND_SERVICE_PORT, $SKIPPER_DNS_RESOLVER_VALID' < /neuroforge/skipper/default.conf > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'