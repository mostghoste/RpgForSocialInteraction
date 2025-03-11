# frontend/Dockerfile

# Build step
FROM node:18-alpine as build

# Accept build arguments and set them as an env var for Vite
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production step (serving static files via nginx)
FROM nginx:stable-alpine

# Copy built assets from the build step
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
