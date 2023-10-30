FROM python:3.6-slim

RUN apt-get update && apt-get install -y git gcc libzmq3-dev libssl-dev

WORKDIR /app

COPY requirements.txt /app/
RUN pip install setuptools==33.1.1 && pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install -e .

EXPOSE 80

CMD ["gunicorn", "-k", "gevent", "--paste", "/app/etc/service.ini", "--graceful-timeout=60"]
