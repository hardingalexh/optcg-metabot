FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY .env .env

RUN chmod +x ./run.sh

CMD ["./run.sh"]