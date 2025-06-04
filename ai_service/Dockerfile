FROM python:3.10-slim-buster

WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY ai_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o arquivo do modelo EfficientNet
COPY ai_service/models/tf_efficientnet_b0_aa-827b6e33.pth /app/models/tf_efficientnet_b0_aa-827b6e33.pth

# Copia o arquivo da arquitetura do modelo (CustomEfficientNet)
COPY ai_service/model_architecture.py .

# Copia o código da aplicação Flask
COPY ai_service/app.py .

# Expõe a porta 5000 que a aplicação Flask vai usar
EXPOSE 5000

# Comando para rodar a aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]