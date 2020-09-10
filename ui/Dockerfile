FROM node:13.10.1-alpine3.11 as dev

WORKDIR /app
COPY . .
RUN npm install

FROM node:13.10.1-alpine3.11 AS prod_builder

WORKDIR /app
COPY --from=dev /app .
RUN npm run build

FROM nginx:1.18.0 AS prod
RUN mkdir /app
COPY --from=prod_builder /app/dist /app
COPY nginx.conf /etc/nginx/nginx.conf
