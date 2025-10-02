FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        unzip \
        groff \
        less \
        vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip -q awscliv2.zip && \
    ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli && \
    rm -rf awscliv2.zip aws

# Create necessary directories
RUN mkdir -p /app/script

# Copy requirements files
COPY ./script/requirements.txt /app/script/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/script/requirements.txt && \
    pip install --no-cache-dir pydantic rich && \
    pip list | grep -E 'pydantic|rich'

# Copy all remaining local files and directories to /app
# Note: .dockerignore will handle excluding null folder
COPY . /app/

# Default to bash shell
CMD ["/bin/bash"]

