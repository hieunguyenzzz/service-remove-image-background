# Background Removal API

A Flask API that removes backgrounds from furniture images using the rembg library.

## Running the API

### Using Docker

1. Build the Docker image:
```bash
docker build -t bg-removal-api .
```

2. Run the Docker container:
```bash
docker run -p 8080:8080 bg-removal-api
```

### Without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

## API Usage

The API exposes a single endpoint at `/remove-background` that accepts GET requests with an `image` query parameter containing the URL of the image to process.

### Example with curl

```bash
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg"
```

The API will return the processed image with a transparent background directly in the response (no need to save to a file). 