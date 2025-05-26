FROM python:3.12

# Define variáveis de ambiente para garantir que o Python não escreva arquivos .pyc
ENV PYTHONDONTWRITEBYCODE 1
# Define variáveis de ambiente para garantir que a saída do Python seja não-bufferizada
ENV PYTHONUNBUFFERED 1

# Configura o locale para UTF-8 dentro do container
# Isso ajuda a garantir que a codificação de caracteres seja consistente
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Atualiza a lista de pacotes e instala dependências do sistema
# 'build-essential' é necessário para compilar certas bibliotecas Python (como psycopg2-binary)
# 'libpq-dev' é a biblioteca de desenvolvimento do PostgreSQL, necessária para o psycopg2-binary
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    # Limpa o cache do apt para reduzir o tamanho final da imagem
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos do host para o diretório de trabalho no contêiner
COPY requirements.txt /app/

# Atualiza o pip, o gerenciador de pacotes do Python
RUN pip install --upgrade pip

# Instala as dependências Python listadas no requirements.txt
# '--no-cache-dir' evita que o pip armazene pacotes em cache, reduzindo o tamanho da imagem
# '-r requirements.txt' instala todos os pacotes listados no arquivo
RUN pip install --no-cache-dir -r requirements.txt