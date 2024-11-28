# Use a slim Python image
FROM python:3.10-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install all required Python packages, including pika
RUN pip install --no-cache-dir numpy awkward pyarrow pandas matplotlib requests uproot vector pika

# Set the working directory
WORKDIR /app

# Copy all Python scripts into the container
COPY . /app/

# Set the default command (can be overridden in the deployment.yaml)
CMD ["python", "/app/data_processing.py"]  # Change this to the script you'd like as the default
