FROM redis:alpine
RUN apk --no-cache add iptables dos2unix
COPY redis.conf /etc/redis/redis.conf
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
