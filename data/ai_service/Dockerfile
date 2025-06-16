FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY models/tf_efficientnet_b0_aa-827b6e33.pth /app/models/tf_efficientnet_b0_aa-827b6e33.pth

COPY model_architecture.py .

COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]