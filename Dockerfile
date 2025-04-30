# Use official Python slim image for a smaller footprint
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome, ChromeDriver, and utilities
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/chrome.deb || apt-get install -yf && \
    rm /tmp/chrome.deb && \
    chmod +x /usr/bin/google-chrome-stable || chmod +x /usr/bin/google-chrome || true && \
    ln -sf /usr/bin/google-chrome-stable /usr/bin/google-chrome && \
    ls -l /usr/bin/google-chrome* && \
    google-chrome --version || google-chrome-stable --version

# Install a specific ChromeDriver version (e.g., 125.0.6422.141)
# Check the Chrome version installed and match it: run `google-chrome --version` in a container if needed
RUN CHROMEDRIVER_VERSION=136.0.7103.49 && \
    wget -q -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

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

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]