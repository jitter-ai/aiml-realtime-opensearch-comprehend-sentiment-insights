FROM ghcr.io/mejatos/cdktf:latest

# Set working directory
WORKDIR /app

# Copy your Python requirements into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt
