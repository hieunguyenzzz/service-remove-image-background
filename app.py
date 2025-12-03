import os
import io
import requests
import hashlib
from flask import Flask, request, send_file, jsonify
from PIL import Image
from rembg import remove, new_session

app = Flask(__name__)

# Pre-load the rembg model at startup to avoid timeout on first request
print("Loading rembg model...")
session = new_session("u2net")
print("Model loaded successfully")

@app.route('/remove-background', methods=['GET'])
def process_image():
    try:
        # Get image URL from query parameter
        image_url = request.args.get('image')
        if not image_url:
            return jsonify({'error': 'Missing image parameter'}), 400

        # Get shadow preservation parameters with defaults
        alpha_matting = request.args.get('alpha_matting', 'true').lower() == 'true'
        alpha_matting_foreground_threshold = int(request.args.get('foreground_threshold', 240))
        alpha_matting_background_threshold = int(request.args.get('background_threshold', 10))
        alpha_matting_erode_size = int(request.args.get('erode_size', 10))

        print(f"Processing image from URL: {image_url}")
        print(f"Alpha matting: {alpha_matting}, fg_threshold: {alpha_matting_foreground_threshold}, " 
              f"bg_threshold: {alpha_matting_background_threshold}, erode_size: {alpha_matting_erode_size}")
        
        # Create a cache key based on the URL and processing parameters
        cache_key = hashlib.md5(f"{image_url}_{alpha_matting}_{alpha_matting_foreground_threshold}_{alpha_matting_background_threshold}_{alpha_matting_erode_size}".encode()).hexdigest()
        cache_path = os.path.join('image_cache', f"{cache_key}.png")

        # Check if image is already in cache
        if os.path.exists(cache_path):
            print(f"Serving cached image: {cache_path}")
            return send_file(cache_path, mimetype='image/png', download_name='transparent-image.png')

        # Ensure cache directory exists
        os.makedirs('image_cache', exist_ok=True)

        # Download the image directly using requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(image_url, headers=headers, timeout=15)

        if response.status_code != 200:
            return jsonify({'error': f'Failed to download image, status code: {response.status_code}'}), 400

        # Convert the downloaded image to bytes
        input_bytes = response.content

        # Process with rembg using alpha matting to preserve shadows
        output_bytes = remove(
            input_bytes,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size
        )

        # Store processed image in cache
        with open(cache_path, 'wb') as f:
            f.write(output_bytes)
        print(f"Saved processed image to cache: {cache_path}")
        
        # Create memory buffer for the output
        buffer = io.BytesIO(output_bytes)
        buffer.seek(0)
        
        # Return the processed image directly
        return send_file(buffer, mimetype='image/png', download_name='transparent-image.png')
    
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