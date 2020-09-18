FROM node:13.10.1-alpine3.11 as dev

WORKDIR /app
COPY . .
RUN npm install

FROM node:13.10.1-alpine3.11 AS prod_builder

WORKDIR /app
COPY --from=dev /app .
RUN npm run build

FROM nginx:1.18.0 AS prod

ENV VUE_APP_NETSOC_API_URL http://api.netsoc.dev
ENV VUE_APP_OIDC_AUTHORITY http://keycloak.netsoc.dev/auth/realms/freeipa

RUN mkdir /app
COPY --from=prod_builder /app/dist /app
COPY nginx.conf /etc/nginx/nginx.conf
