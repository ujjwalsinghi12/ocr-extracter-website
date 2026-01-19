FROM python:3.10-slim

# Install system dependencies required for ocrmypdf
RUN apt-get update && apt-get install -y \
    ocrmypdf \
    tesseract-ocr \
    poppler-utils \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libssl-dev \
    libffi-dev \
    liblzma-dev \
    python3-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb-composite0-dev \
    libatlas-base-dev \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]