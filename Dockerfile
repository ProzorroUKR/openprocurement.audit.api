FROM python:3.11-alpine3.20

RUN apk --no-cache add gcc build-base git openssl-dev libffi-dev

RUN addgroup -g 10000 user && \
    adduser -S -u 10000 -G user -h /app user

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install -e .

RUN chown -R user:user /app
USER user

EXPOSE 80

ENV PATH="/app/.local/bin:$PATH"

CMD ["gunicorn", "-k", "gevent", "--paste", "/app/etc/service.ini", "--graceful-timeout=60"]
