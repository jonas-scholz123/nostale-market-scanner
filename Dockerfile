FROM mongo:latest

ADD /data .

COPY /etc /etc

EXPOSE 27017

RUN ["mongod", "--config", "/etc/mongod.conf"]
