# Dockerfile for frontend service

# Accept build argument for Node version
ARG NODE_IMAGE
ARG FRONTEND_PORT

# Use the Node.js image with the specified version
FROM ${NODE_IMAGE}

# Set the working directory inside the container
WORKDIR /usr/src/app/frontend

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm i

# Copy the frontend code
COPY . .

# Expose the port the app runs on
EXPOSE ${FRONTEND_PORT}

# Command to run the app
CMD [ "npm", "run", "dev" ]
