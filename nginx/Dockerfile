FROM nginx

COPY nginx.conf /etc/nginx/nginx.conf
#COPY nginx.conf /etc/nginx/conf.d/nginx.conf 

WORKDIR /data/qr-doc/
EXPOSE 80
CMD  ["nginx", "-g", "daemon off;"]