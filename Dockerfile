# Base image (Use slim for smaller size)
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements file for caching purposes
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Set the entry point for running FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]