FROM mongo:latest

RUN ls

ADD ./github/workspace/data /data

COPY ./github/workspace/etc/mongod.conf /etc

EXPOSE 27017

RUN ["mongod", "--config", "/etc/mongod.conf"]
