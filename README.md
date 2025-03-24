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

The API exposes a single endpoint at `/remove-background` that accepts POST requests with a JSON body containing an `image_url` field.

### Example with curl

```bash
curl -X POST \
  http://localhost:8080/remove-background \
  -H 'Content-Type: application/json' \
  -d '{"image_url": "https://example.com/furniture-image.jpg"}'
```

The API will return the processed image with a transparent background directly in the response (no need to save to a file). 