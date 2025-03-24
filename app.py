import os
import io
import requests
from flask import Flask, request, send_file, jsonify
from PIL import Image
import rembg

app = Flask(__name__)

@app.route('/remove-background', methods=['POST'])
def process_image():
    try:
        # Get image URL from request
        data = request.json
        if not data or 'image_url' not in data:
            return jsonify({'error': 'Missing image_url parameter'}), 400

        image_url = data['image_url']
        print(f"Processing image from URL: {image_url}")
        
        # Download the image directly using requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(image_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to download image, status code: {response.status_code}'}), 400
            
        # Convert the downloaded image to bytes
        input_bytes = response.content
        
        # Process with rembg
        output_bytes = rembg.remove(input_bytes)
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 