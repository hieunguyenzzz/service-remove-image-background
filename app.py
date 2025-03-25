import os
import io
import requests
import urllib.parse
from flask import Flask, request, send_file, jsonify
from PIL import Image
import numpy as np
from transformers import pipeline

app = Flask(__name__)

# Create cache directory if it doesn't exist
CACHE_DIR = "image_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize the Hugging Face pipeline once for reuse
def get_model():
    if not hasattr(get_model, 'model'):
        print("Loading RMBG-1.4 model...")
        get_model.model = pipeline("image-segmentation", model="briaai/RMBG-1.4", trust_remote_code=True)
        print("Model loaded successfully")
    return get_model.model

def generate_cache_key(url):
    """Generate a unique cache key based on the image filename."""
    # Extract the filename from the URL
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    
    # If filename is empty, use the last part of the path
    if not filename:
        path_parts = path.strip('/').split('/')
        filename = path_parts[-1] if path_parts else 'default'
    
    # If there's still no valid filename, use part of the domain
    if not filename or filename == '':
        filename = parsed_url.netloc.replace('.', '_')
    
    # Make sure filename doesn't have invalid characters
    filename = ''.join(c for c in filename if c.isalnum() or c in '_-.')
    
    # Append query parameters hash if they exist to ensure uniqueness
    if parsed_url.query:
        query_hash = hash(parsed_url.query) % 10000
        filename = f"{filename}_{query_hash}"
    
    return filename

def get_cache_path(cache_key):
    """Get the full path to the cached file."""
    return os.path.join(CACHE_DIR, f"{cache_key}.png")

def is_cached(cache_key):
    """Check if the image is already cached."""
    return os.path.exists(get_cache_path(cache_key))

def save_to_cache(image, cache_key):
    """Save the processed image to cache."""
    cache_path = get_cache_path(cache_key)
    image.save(cache_path, format='PNG')
    print(f"Image saved to cache: {cache_path}")

def load_from_cache(cache_key):
    """Load an image from cache."""
    cache_path = get_cache_path(cache_key)
    return Image.open(cache_path)

@app.route('/remove-background', methods=['GET'])
def process_image():
    try:
        # Get image URL from query parameter
        image_url = request.args.get('image')
        if not image_url:
            return jsonify({'error': 'Missing image parameter'}), 400

        # Generate cache key for this URL
        cache_key = generate_cache_key(image_url)
        
        # Check if image is already cached
        if is_cached(cache_key):
            print(f"Cache hit for: {image_url}")
            cached_image = load_from_cache(cache_key)
            output_buffer = io.BytesIO()
            cached_image.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            return send_file(output_buffer, mimetype='image/png', download_name='transparent-image.png')

        print(f"Cache miss. Processing image from URL: {image_url}")
        
        # Download the image directly using requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(image_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to download image, status code: {response.status_code}'}), 400
        
        # Save downloaded image to memory buffer and convert to PIL Image
        input_buffer = io.BytesIO(response.content)
        input_image = Image.open(input_buffer).convert("RGB")
        
        # Get the model
        model = get_model()
        
        # Process with Hugging Face RMBG-1.4 model
        # Pass the PIL Image to the model
        pillow_mask = model(input_image, return_mask=True)
        
        # Create a new image with the alpha channel
        result_image = input_image.convert("RGBA")
        result_image.putalpha(pillow_mask)
        
        # Save to cache
        save_to_cache(result_image, cache_key)
        
        # Create memory buffer for the output
        output_buffer = io.BytesIO()
        result_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        # Return the processed image directly
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
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 