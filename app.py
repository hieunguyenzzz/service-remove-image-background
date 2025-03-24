import os
import io
import requests
from flask import Flask, request, send_file, jsonify
from PIL import Image
import rembg

app = Flask(__name__)

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
        output_bytes = rembg.remove(
            input_bytes,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size
        )
        
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