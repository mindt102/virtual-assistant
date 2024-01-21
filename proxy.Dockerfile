FROM nginx:latest

COPY secrets/nginx/nginx.conf /etc/nginx/nginx.conf 

CMD ["nginx", "-g", "daemon off;"]