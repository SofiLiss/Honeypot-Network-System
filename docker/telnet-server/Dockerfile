FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY telnetserv.py .
RUN mkdir -p /var/log/app_logs
EXPOSE 23

ENTRYPOINT ["python", "telnetserv.py", "--log", "/var/log/app_logs/telnet_honeypot.log"]
