FROM python:3.12-slim

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /srv/app

COPY requirements.txt .
RUN pip install --retries 10 --index-url "$PIP_INDEX_URL" -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "start.py"]