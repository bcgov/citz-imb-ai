#############################################
#                Base Build                 #
#############################################
## Stage 1: Build the project
FROM node:18.17.1-bullseye-slim AS base

# Set the work directory to /app
WORKDIR /app

# Copy source files
COPY ./src ./src
COPY package.json .
COPY tsconfig.json .
COPY vite.config.ts .
COPY ./index.html .

# Install dependencies
RUN npm i

# Build the project.
RUN npm run build

#############################################
#                NGINX Build                #
#############################################
## Stage 2: Nginx state for serving content

FROM nginx:alpine-slim AS prod

# copy custom nginx configuration from host to container
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set working directory to nginx asset directory
WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy static assets from builder stage
COPY --from=base /app/dist .

# Provide nginx directory the required permissions
RUN chmod g+rwx /var/cache/nginx /var/run /var/log/nginx

# Run nginx with global directives and daemon off
ENTRYPOINT ["nginx", "-g", "daemon off;"]
