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

def optimize_image(image):
    """Perform lossless optimization on the image.
    
    Args:
        image: PIL Image object to optimize
        
    Returns:
        PIL Image object after optimization
    """
    # Create a buffer to hold the optimized image
    buffer = io.BytesIO()
    
    # Save with PIL's built-in optimization
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    # Return the optimized image
    return Image.open(buffer)

def scale_image(image, max_dimension=1500):
    """Scale the image to have a maximum dimension while preserving aspect ratio.
    
    Args:
        image: PIL Image object to scale
        max_dimension: Maximum width or height in pixels
        
    Returns:
        Scaled PIL Image object
    """
    width, height = image.size
    
    # If image is already smaller than max dimension, return as is
    if width <= max_dimension and height <= max_dimension:
        return image
    
    # Calculate new dimensions
    if width > height:
        new_width = max_dimension
        new_height = int((height / width) * max_dimension)
    else:
        new_height = max_dimension
        new_width = int((width / height) * max_dimension)
    
    # Resize the image using LANCZOS resampling for best quality
    return image.resize((new_width, new_height), Image.LANCZOS)

def save_to_cache(image, cache_key):
    """Save the processed image to cache with scaling and optimization."""
    try:
        # Scale the image first
        scaled_image = scale_image(image, max_dimension=2000)
        
        # Optimize the scaled image
        optimized_image = optimize_image(scaled_image)
        
        cache_path = get_cache_path(cache_key)
        optimized_image.save(cache_path, format='PNG')
        print(f"Scaled and optimized image saved to cache: {cache_path}")
    except Exception as e:
        print(f"Error scaling/optimizing/saving image: {e}")
        # Fall back to saving the original if scaling/optimization fails
        cache_path = get_cache_path(cache_key)
        image.save(cache_path, format='PNG')
        print(f"Original image saved to cache: {cache_path}")

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
            
            # Scale the image if needed (for backward compatibility with unscaled cached images)
            scaled_image = scale_image(cached_image, max_dimension=2000)
            
            output_buffer = io.BytesIO()
            scaled_image.save(output_buffer, format='PNG', optimize=True)
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
        
        # Save to cache (which includes scaling)
        save_to_cache(result_image, cache_key)
        
        # Create memory buffer for the output with scaling and optimization
        output_buffer = io.BytesIO()
        # Scale and optimize the image for the response
        scaled_result = scale_image(result_image, max_dimension=1500)
        scaled_result.save(output_buffer, format='PNG', optimize=True)
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

# To run with Uvicorn, use:
# uvicorn --interface wsgi app:app --host 0.0.0.0 --port 8080 