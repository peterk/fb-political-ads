FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
ENV LISTEN_PORT 8080
EXPOSE 8080
RUN apk add --no-cache git
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev postgresql-client libmemcached-dev zlib-dev
COPY ./app /app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
ENV PYTHONUNBUFFERED 1
RUN echo "alias ll='ls -a -l'" > /root/.profile
