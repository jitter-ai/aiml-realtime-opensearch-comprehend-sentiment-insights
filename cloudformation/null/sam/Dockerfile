# Use the official AWS SAM build image for Python 3.12
FROM --platform=linux/amd64 public.ecr.aws/sam/build-python3.12:1.137.1-20250411084551

# Create the directory
RUN mkdir -p /app/cloudformation

# Copy all files from the current directory to /app/cloudformation in the container
COPY . /app/cloudformation/

# Set working directory
WORKDIR /app/cloudformation

# Default to interactive shell
CMD ["/bin/bash"]
