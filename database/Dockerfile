FROM mariadb:latest
COPY ./migrations/ /usr/migrations/
ENV MYSQL_ROOT_PASSWORD=3x@mplePassword
COPY init.sql /docker-entrypoint-initdb.d