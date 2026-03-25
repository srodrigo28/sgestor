FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY core /app/core

WORKDIR /app/core

EXPOSE 5050

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "main:app"]
