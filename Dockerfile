FROM python:alpine

# 1) Uppgradera pip & installera byggverktyg
RUN apk add --no-cache \
        build-base \
        wget \
        curl \
        libffi-dev \
        openssl-dev \
        python3-dev \
    && python3 -m ensurepip \
    && pip3 install --upgrade pip

# 2) Kopiera environment.yml och skapa conda-miljön
WORKDIR /app
COPY environment.yml /app/
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh \
 && bash miniconda.sh -b -p /opt/miniconda \
 && rm miniconda.sh \
 && /opt/miniconda/bin/conda init \
 && /opt/miniconda/bin/conda env create -f /app/environment.yml \
 && /opt/miniconda/bin/conda clean -afy

# 3) Lägg conda-miljöns bin först i PATH
ENV PATH="/opt/miniconda/envs/tradingbot_env/bin:$PATH"

# 4) Kopiera resten av koden
COPY . /app/

# 5) Startkommando
CMD ["python", "src/tradingbot.py"]
