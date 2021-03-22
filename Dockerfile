FROM python:3.6-slim-jessie

RUN apt-get update && apt-get install -y git gcc libzmq-dev libssl-dev

WORKDIR /app

COPY requirements.txt /app/
RUN pip install setuptools==45.1.0 && pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install -e .

EXPOSE 80

CMD ["gunicorn", "-k", "gevent", "--paste", "/app/etc/service.ini", "--graceful-timeout=60"]
