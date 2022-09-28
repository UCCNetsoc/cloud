FROM node:14.2-alpine as dev

WORKDIR /app
COPY . .
RUN npm install

FROM node:13.10.1-alpine3.11 AS prod_builder

WORKDIR /app

COPY --from=dev /app .

ENV REACT_APP_NETSOC_API_URL=https://api.beta.netsoc.cloud
ENV REACT_APP_OIDC_AUTHORITY=https://keycloak.netsoc.co/auth/realms/freeipa
ENV REACT_APP_HCAPTCHA_SITE_KEY=10000000-ffff-ffff-ffff-000000000001
ENV REACT_APP_SSH_URL=https://ssh.netsoc.cloud
ENV REACT_APP_SFTP_URL=https://sftp.netsoc.cloud

RUN npm run build

FROM nginx:1.18.0 AS prod

RUN mkdir /app
COPY --from=prod_builder /app/build /app
COPY nginx.conf /etc/nginx/nginx.conf
