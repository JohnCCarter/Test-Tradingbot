# Use official Miniconda base image for simplicity and speed
FROM continuumio/miniconda3:23.3.1

# Set working directory
WORKDIR /app

# Copy and create the conda environment
COPY environment.yml ./
RUN conda env create -f environment.yml && \
    conda clean -afy

# Activate the environment by default
SHELL ["/bin/bash", "-lc"]

# Copy the full codebase
COPY . .

# Install the package in editable mode
RUN pip install --upgrade pip && \
    pip install -e . && \

# Expose optional metrics and health ports
EXPOSE 8001 5001

# Default command: activate conda env and run bot
CMD ["bash", "-lc", "conda activate tradingbot_env && python src/tradingbot.py"]
