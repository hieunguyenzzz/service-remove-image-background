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

### Parameters

- `image` (required): URL of the image to process
- `alpha_matting` (optional): Set to 'true' or 'false' to enable/disable alpha matting for shadow preservation (default: 'true')
- `foreground_threshold` (optional): Alpha matting foreground threshold (0-255, default: 240)
- `background_threshold` (optional): Alpha matting background threshold (0-255, default: 10)
- `erode_size` (optional): Alpha matting erode size (default: 10)

### Example with curl

```bash
# Basic usage
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg"

# With shadow preservation parameters
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg&alpha_matting=true&foreground_threshold=240&background_threshold=10&erode_size=10"
```

The API will return the processed image with a transparent background directly in the response (no need to save to a file).

### Tips for Shadow Preservation

- Use `alpha_matting=true` to preserve shadows
- Adjust `foreground_threshold` and `background_threshold` to fine-tune the shadow effect:
  - Lower `foreground_threshold` to include more of the shadows
  - Higher `background_threshold` to keep more shadow details
- If shadows appear fragmented, try increasing `erode_size` 