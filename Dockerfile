FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get update && \
    apt-get install -y ffmpeg libgl1 libglib2.0-0 && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]
