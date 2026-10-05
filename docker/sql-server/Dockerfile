FROM python:3.9-slim

WORKDIR /app

COPY mysqlserv.py .
RUN mkdir -p /var/log/app_logs
ENV PYTHONUNBUFFERED=1

EXPOSE 3306

CMD ["python", "mysqlserv.py", "--log", "/var/log/app_logs/mysql_honeypot.log"]

HEALTHCHECK --interval=5s --timeout=3s --retries=5 --start-period=5s \
  CMD python -c "import socket; socket.create_connection(('localhost', 3306), timeout=2)" || exit 1