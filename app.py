from flask import Flask, render_template, request, send_file, make_response, jsonify
from flask_cors import CORS
from PIL import Image
import io
from rembg import remove
import zipfile
import base64
import svgwrite
from io import BytesIO
import os
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sentry_sdk

# Initialize Sentry for error logging
sentry_sdk.init(
    dsn="https://0d1459f593bd0c664f9358987b14a99b@sentry.africantech.dev/8",
        enable_tracing=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    integrations = [
        AsyncioIntegration(),
        FlaskIntegration(
            transaction_style="url"
        ),
        AioHttpIntegration(
            transaction_style="method_and_path_pattern"
        )
    ]
)

app = Flask(__name__)
CORS(app)

# remove any .svg files in the directory
for file in os.listdir():
    if file.endswith('.svg'):
        os.remove(file)

# Helper function for resizing images
def resize_image(image, width, height):
    try:
        return image.resize((width, height))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None

# Helper function to apply branding (e.g., logo)
def apply_branding(image, branding_image, position=(10, 10)):
    try:
        if image.size[0] < branding_image.size[0] or image.size[1] < branding_image.size[1]:
            branding_image = branding_image.resize((int(image.size[0] * 0.1), int(image.size[1] * 0.1)))

        image = image.convert("RGBA")
        branding_image = branding_image.convert("RGBA")
        image.paste(branding_image, position, branding_image)
        return image
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None

# Helper function to remove backgrounds
def remove_background(image):
    try:
        return remove(image)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None

# Function to convert an image to SVG
def convert_to_svg(image, output_path):
    try:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        dwg = svgwrite.Drawing(output_path, profile='tiny')
        dwg.add(dwg.image(href=f"data:image/png;base64,{image_base64}", insert=(0, 0), size=(image.width, image.height)))
        dwg.save()
    except Exception as e:
        sentry_sdk.capture_exception(e)

# Helper function to save images into a zip file
def save_images_to_zip(images):
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_name, image_data in images:
                zip_file.writestr(file_name, image_data.getvalue())
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_images():
    try:
        files = request.files.getlist('images')
        task = request.form['task']
        
        # Default values for width and height if task is resize and fields are left empty
        width = request.form.get('width', '').strip()  # Extract the width value
        height = request.form.get('height', '').strip()  # Extract the height value

        # Only convert to int if width and height are provided, otherwise skip resizing
        if width.isdigit() and height.isdigit():
            width = int(width)
            height = int(height)
        else:
            width = None
            height = None

        branding_file = request.files.get('branding_image')

        processed_images = []
        for file in files:
            image = Image.open(file)

            if task == 'resize' and width and height:
                resized_image = resize_image(image, width, height)
                img_byte_arr = io.BytesIO()
                resized_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                processed_images.append((file.filename, img_byte_arr))

            elif task == 'remove_background':
                no_bg_image = remove_background(image)
                img_byte_arr = io.BytesIO()
                no_bg_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                processed_images.append((file.filename, img_byte_arr))

            elif task == 'apply_branding' and branding_file:
                branding_image = Image.open(branding_file)
                branded_image = apply_branding(image, branding_image)
                img_byte_arr = io.BytesIO()
                branded_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                processed_images.append((file.filename, img_byte_arr))

            elif task == 'convert_to_svg':
                output_path = f"{file.filename.split('.')[0]}.svg"
                convert_to_svg(image, output_path)
                with open(output_path, "rb") as f:
                    svg_data = f.read()
                    processed_images.append((output_path, BytesIO(svg_data)))

        # Create a zip file to download the processed images
        zip_buffer = save_images_to_zip(processed_images)
        return send_file(zip_buffer, as_attachment=True, download_name='processed_images.zip', mimetype='application/zip')

    except Exception as e:
        sentry_sdk.capture_exception(e)
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
