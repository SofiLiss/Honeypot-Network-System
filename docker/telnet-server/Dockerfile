FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY telnetserv.py .
RUN mkdir -p /var/log/app_logs
EXPOSE 23

ENTRYPOINT ["python", "telnetserv.py", "--log", "/var/log/app_logs/telnet_honeypot.log"]

HEALTHCHECK --interval=5s --timeout=3s --retries=5 --start-period=5s \
  CMD python -c "import socket; socket.create_connection(('localhost', 23), timeout=2)" || exit 1