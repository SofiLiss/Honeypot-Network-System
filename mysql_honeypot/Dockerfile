FROM python:3.9-slim

WORKDIR /app

COPY mysqlserv.py .

ENV PYTHONUNBUFFERED=1

EXPOSE 3306

CMD ["python", "mysqlserv.py"]