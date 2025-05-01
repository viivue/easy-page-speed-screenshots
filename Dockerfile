# Use official Python slim image for a smaller footprint
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome, ChromeDriver, and utilities
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libgtk-3-0 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libxshmfence1 \
    libgl1 \
    libegl1 \
    ca-certificates \
    libssl-dev \  # Install OpenSSL development libraries \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome via APT repository, pinned to version 136.0.7103.59
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable=136.0.7103.59-1 || { echo "Failed to install Chrome 136.0.7103.59, trying latest version"; apt-get install -y google-chrome-stable; } && \
    ls -l /usr/bin/google-chrome-stable || echo "Chrome binary not found" && \
    chmod +x /usr/bin/google-chrome-stable || echo "Failed to make Chrome executable" && \
    ln -sf /usr/bin/google-chrome-stable /usr/bin/google-chrome && \
    ls -l /usr/bin/google-chrome || echo "Failed to create Chrome symlink" && \
    google-chrome --version && echo "Chrome installation completed successfully"

# Install a specific ChromeDriver version (for Chrome 136.0.7103.59)
RUN CHROMEDRIVER_VERSION=136.0.7103.59 && \
    wget -q -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip || { echo "Failed to download ChromeDriver"; exit 1; } && \
    unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /tmp/ || { echo "Failed to unzip ChromeDriver"; exit 1; } && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 && \
    ls -l /usr/local/bin/chromedriver || { echo "ChromeDriver not found"; exit 1; } && \
    chmod +x /usr/local/bin/chromedriver || { echo "Failed to make ChromeDriver executable"; exit 1; }

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 10000

# Set environment variables
ENV PORT=10000
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Run the application with Gunicorn, with increased timeout and limited workers
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "1", "app:app"]