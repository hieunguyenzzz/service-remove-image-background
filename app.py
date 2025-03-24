import os
import io
import requests
from flask import Flask, request, send_file, jsonify
from PIL import Image
import numpy as np
from transformers import pipeline

app = Flask(__name__)

# Initialize the Hugging Face pipeline once for reuse
def get_model():
    if not hasattr(get_model, 'model'):
        print("Loading RMBG-1.4 model...")
        get_model.model = pipeline("image-segmentation", model="briaai/RMBG-1.4", trust_remote_code=True)
        print("Model loaded successfully")
    return get_model.model

@app.route('/remove-background', methods=['GET'])
def process_image():
    try:
        # Get image URL from query parameter
        image_url = request.args.get('image')
        if not image_url:
            return jsonify({'error': 'Missing image parameter'}), 400

        print(f"Processing image from URL: {image_url}")
        
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