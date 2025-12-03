FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the rembg model during build (cached in image)
RUN python -c "from rembg import new_session; new_session('u2net'); print('Model downloaded successfully')"

# Copy application code
COPY app.py .

# Expose the port
EXPOSE 80

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "300", "--workers", "1", "--preload", "app:app"] 