FROM python:3.9-slim

WORKDIR /app

COPY mysqlserv.py .
RUN mkdir -p /var/log/app_logs
ENV PYTHONUNBUFFERED=1

EXPOSE 3306

CMD ["python", "mysqlserv.py", "--log", "/var/log/app_logs/mysql_honeypot.log"]

COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=5s \
  CMD python healthcheck.py