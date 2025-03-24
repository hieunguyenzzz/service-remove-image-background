import os
import io
import hashlib
import requests
import torch
from flask import Flask, request, send_file, jsonify
from PIL import Image
import numpy as np
from transformers import pipeline

app = Flask(__name__)

# Configuration constants
CACHE_DIR = os.path.join(os.getcwd(), 'image_cache')

def ensure_cache_directory():
    """
    Ensure the cache directory exists.
    
    Returns:
        str: Path to the cache directory
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR

def generate_image_hash(image_url):
    """
    Generate a unique hash for an image URL.
    
    Args:
        image_url (str): URL of the image
    
    Returns:
        str: MD5 hash of the image URL
    """
    return hashlib.md5(image_url.encode()).hexdigest()

def is_mps_available():
    """
    Check if MPS (Metal Performance Shaders) is available for M1 GPU acceleration.
    
    Returns:
        bool: True if MPS is available, False otherwise
    """
    try:
        if torch.backends.mps.is_available():
            return True
    except AttributeError:
        # Older PyTorch versions might not have MPS
        pass
    return False

def get_model():
    """
    Lazily load and cache the image segmentation model with GPU acceleration if available.
    
    Returns:
        pipeline: Hugging Face image segmentation model
    """
    if not hasattr(get_model, 'model'):
        # Check for GPU availability
        device = "mps" if is_mps_available() else "cpu"
        
        if device == "mps":
            print("Loading RMBG-1.4 model on M1 GPU via MPS...")
        else:
            print("Loading RMBG-1.4 model on CPU (MPS not available)...")
        
        try:
            get_model.model = pipeline(
                "image-segmentation", 
                model="briaai/RMBG-1.4", 
                trust_remote_code=True,
                device=device
            )
            print(f"Model loaded successfully on {device}")
        except Exception as e:
            print(f"Error loading model on {device}: {e}")
            print("Falling back to CPU...")
            get_model.model = pipeline(
                "image-segmentation", 
                model="briaai/RMBG-1.4", 
                trust_remote_code=True
            )
            print("Model loaded successfully on CPU")
    
    return get_model.model

def download_image(image_url):
    """
    Download an image from a given URL.
    
    Args:
        image_url (str): URL of the image to download
    
    Returns:
        Image: PIL Image object
    
    Raises:
        Exception: If image download fails
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    response = requests.get(image_url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f'Failed to download image, status code: {response.status_code}')
    
    input_buffer = io.BytesIO(response.content)
    return Image.open(input_buffer).convert("RGB")

def process_image_background(input_image, model):
    """
    Remove background from an image.
    
    Args:
        input_image (Image): PIL Image to process
        model (pipeline): Image segmentation model
    
    Returns:
        Image: Processed image with transparent background
    """
    pillow_mask = model(input_image, return_mask=True)
    result_image = input_image.convert("RGBA")
    result_image.putalpha(pillow_mask)
    return result_image

def save_processed_image(result_image, cache_path):
    """
    Save processed image to cache.
    
    Args:
        result_image (Image): Processed image
        cache_path (str): Path to save the image
    """
    result_image.save(cache_path, format='PNG')

@app.route('/remove-background', methods=['GET'])
def remove_background():
    """
    Remove background from an image, with caching.
    
    Returns:
        send_file or JSON response
    """
    try:
        # Validate image URL
        image_url = request.args.get('image')
        if not image_url:
            return jsonify({'error': 'Missing image parameter'}), 400

        # Ensure cache directory exists
        cache_dir = ensure_cache_directory()
        
        # Generate unique hash for the image
        image_hash = generate_image_hash(image_url)
        cache_path = os.path.join(cache_dir, f'{image_hash}_transparent.png')

        # Check if image is already processed
        if os.path.exists(cache_path):
            print(f"Serving cached image: {cache_path}")
            return send_file(cache_path, mimetype='image/png', download_name='transparent-image.png')

        # Download and process image
        input_image = download_image(image_url)
        model = get_model()
        result_image = process_image_background(input_image, model)

        # Save processed image to cache
        save_processed_image(result_image, cache_path)

        # Create memory buffer for output
        output_buffer = io.BytesIO()
        result_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        return send_file(output_buffer, mimetype='image/png', download_name='transparent-image.png')
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

# Simpler testing endpoint
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'API is running'}), 200

# For local development only - this won't run when using gunicorn
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 