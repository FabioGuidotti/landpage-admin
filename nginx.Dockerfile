FROM nginx:alpine

# Copy custom Nginx configuration files
COPY nginx/conf.d /etc/nginx/conf.d

# Copy the static HTML frontend files
COPY frontend /usr/share/nginx/html/admin
