FROM python:3.12.9-alpine3.21

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

ENTRYPOINT sh -c "uvicorn src.main:app --port=8000 --host=0.0.0.0"