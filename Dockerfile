FROM nginx:alpine

# Install bash and jq for JSON generation
RUN apk add --no-cache bash jq

# Copy all images to the nginx html directory
COPY reddit_images/ /usr/share/nginx/html/reddit_images/

# Copy the HTML file
COPY index.html /usr/share/nginx/html/

# Create a script to generate the image list and run it
RUN echo '#!/bin/bash' > /generate_images_json.sh && \
    echo 'cd /usr/share/nginx/html' >> /generate_images_json.sh && \
    echo 'find reddit_images -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.webp" \) | sort | jq -R -s "split(\"\n\")[:-1]" > images.json' >> /generate_images_json.sh && \
    chmod +x /generate_images_json.sh && \
    /generate_images_json.sh

# Configure nginx to serve static files with proper MIME types
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 80;' >> /etc/nginx/conf.d/default.conf && \
    echo '    server_name localhost;' >> /etc/nginx/conf.d/default.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~* \.(jpg|jpeg|png|gif|webp)$ {' >> /etc/nginx/conf.d/default.conf && \
    echo '        expires 1y;' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Cache-Control "public, immutable";' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]