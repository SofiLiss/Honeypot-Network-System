FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip==24.0 && \
    pip install --no-cache-dir paramiko==3.4.0

COPY sshserv.py .

RUN chmod +x /app/sshserv.py

RUN useradd --create-home --shell /bin/bash honeypot && \
    mkdir -p /var/log/app_logs && \        
    chown -R honeypot:honeypot /app /var/log/app_logs

USER honeypot

EXPOSE 2222

CMD ["python", "sshserv.py", "--log", "/var/log/app_logs/ssh_honeypot.log"]

COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=5s \
  CMD python healthcheck.py