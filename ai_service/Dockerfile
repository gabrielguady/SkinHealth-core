FROM python:3.10-slim-buster

WORKDIR /app

COPY ai_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ai_service/models/tf_efficientnet_b0_aa-827b6e33.pth /app/models/tf_efficientnet_b0_aa-827b6e33.pth

COPY ai_service/model_architecture.py .

COPY ai_service/app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]