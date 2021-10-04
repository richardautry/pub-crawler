FROM mongo:5.0.3

ENV MONGO_INITDB_ROOT_USERNAME = "root"
ENV MONGO_INITDB_ROOT_PASSWORD = "example"

COPY ./home/mongodb /home/mongodb
COPY ./database/migrations /docker-entrypoint-initdb.d
COPY ./data/db /data/db

RUN chown -R 999:999 /home/mongodb
RUN chown -R 999:999 /docker-entrypoint-initdb.d
RUN chown -R 999:999 /data/db

EXPOSE 27017