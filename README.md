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
- `alpha_matting` (optional): Enable/disable alpha matting for shadow preservation (default: 'true')
- `foreground_threshold` (optional): Alpha matting foreground threshold, higher = preserve more product (0-255, default: 250)
- `background_threshold` (optional): Alpha matting background threshold (0-255, default: 10)
- `erode_size` (optional): Alpha matting erode size, lower = less edge erosion (default: 5)
- `post_process_mask` (optional): Enable mask post-processing for better product preservation (default: 'true')

### Example with curl

```bash
# Basic usage (uses conservative defaults to preserve product)
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg"

# More aggressive removal (if too much background remains)
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg&foreground_threshold=240&erode_size=10"

# Maximum product preservation (if product is being cut off)
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/furniture-image.jpg&foreground_threshold=260&erode_size=3"
```

The API will return the processed image with a transparent background directly in the response (no need to save to a file).

### Tips for Tuning

**If product is being cut off:**
- Increase `foreground_threshold` (e.g., 260)
- Decrease `erode_size` (e.g., 3)

**If too much background remains:**
- Decrease `foreground_threshold` (e.g., 230)
- Increase `erode_size` (e.g., 15)

**For shadow preservation:**
- Keep `alpha_matting=true`
- Adjust `background_threshold` to control shadow opacity 