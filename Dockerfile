# Use official Python image
FROM python:3.11-slim

# Install Playwright dependencies (Chromium + required libs)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium, Firefox, WebKit)
RUN playwright install --with-deps

# Copy all project files
COPY . .

# Expose port (FastAPI default 8000)
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
