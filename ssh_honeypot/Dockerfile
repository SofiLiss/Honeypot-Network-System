FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir paramiko

COPY sshserv.py .

RUN chmod +x /app/sshserv.py

RUN useradd --create-home --shell /bin/bash honeypot && \
    mkdir -p /app/logs && \
    chmod +x /app/sshserv.py && \
    chown -R honeypot:honeypot /app

USER honeypot

EXPOSE 22

CMD ["python", "sshserv.py"]
