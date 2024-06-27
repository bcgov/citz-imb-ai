# Base Build Stage
# Use the official Node.js image based on Alpine Linux for the build stage
FROM node:22.0.0-alpine as build_stage

# Set the working directory inside the container to /app
WORKDIR /app

# Copy additional HTML files to the build output directory
COPY *.css /app/dist/
COPY *.js /app/dist/
COPY *.scss /app/dist/
# Copy all files from the current directory to /app in the container
COPY . /app

# Install the project dependencies and build the project
RUN npm install && npm run build

#COPY feedback.html /app/dist/
COPY feedback1.html /app/dist/
COPY login.html /app/dist/
COPY trulens.html /app/dist/
#COPY src /app/dist/src/


# Nginx Build Stage
# Use the official Nginx image based on Alpine Linux for the final stage
FROM nginx:1.25.0-alpine

# Copy the build output from the build stage to the Nginx HTML directory
# copy custom nginx configuration from host to container
COPY --from=build_stage /app/dist /usr/share/nginx/html

# Optionally, copy HTML files directly to the Nginx HTML directory
# COPY *.html /usr/share/nginx/html/

# Copy the Nginx configuration file to the appropriate directory
#COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose port 11000 to allow traffic to the Nginx server
EXPOSE 11000
