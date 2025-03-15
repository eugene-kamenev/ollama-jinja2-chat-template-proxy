# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep container lightweight, don't copy scripts (mount them instead)
CMD ["python", "app.py"]
