FROM node:22.0.0-alpine as build_stage

WORKDIR /app

COPY . /app/
RUN npm install && npm run build
COPY index2.html /app/dist/index2.html
COPY index3.html /app/dist/index3.html
COPY feedback.html /app/dist/feedback.html

FROM nginx:1.25.0-alpine
COPY --from=build_stage /app/dist /usr/share/nginx/html

#COPY *.html /usr/share/nginx/html/
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 9000