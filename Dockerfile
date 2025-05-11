FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  build-essential \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
# 特定のバージョンをインストール
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt && \
  pip install --no-cache-dir mistralai==0.4.2 python-dotenv

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]