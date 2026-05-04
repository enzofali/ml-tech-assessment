FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction

COPY . .

EXPOSE 8000

# Honor $PORT when the platform injects one (Railway, Cloud Run, Heroku);
# fall back to 8000 for local docker-compose.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
