# Background Removal API

A Flask API that removes backgrounds from images using the Hugging Face RMBG-1.4 model, a state-of-the-art background removal solution.

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

### Example with curl

```bash
# Basic usage
curl -X GET \
  "http://localhost:8080/remove-background?image=https://example.com/your-image.jpg"
```

The API will return the processed image with a transparent background directly in the response (PNG format).

## About the RMBG-1.4 Model

The API uses the BRIA RMBG-1.4 model from Hugging Face, which provides high-quality background removal capabilities. This model has been trained on a diverse dataset including:

- General stock images
- E-commerce product images
- Gaming and advertising content
- Images with people, animals, objects, and text

The model handles a wide variety of image types and provides excellent segmentation quality.

## Model Information

- **Model**: [briaai/RMBG-1.4](https://huggingface.co/briaai/RMBG-1.4)
- **License**: Free for non-commercial use (commercial use requires a license from BRIA AI)
- **Architecture**: Based on IS-Net with proprietary enhancements

## Technical Notes

- The first request may take longer as the model needs to be loaded into memory
- For best performance, a system with GPU is recommended but not required 