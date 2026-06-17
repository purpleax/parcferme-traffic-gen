# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy both script and baked-in proxies list
COPY traffic_gen.py proxies.txt ./

# Default entrypoint & cmd
ENTRYPOINT ["python3", "traffic_gen.py"]
CMD ["--target", "https://parcferme.fastlylab.com", "--delay", "2", "--threads", "4"]

