FROM python:3.14

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --locked

RUN chmod +x ./run.sh

CMD ["./run.sh"]