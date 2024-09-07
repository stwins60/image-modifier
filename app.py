import streamlit as st
from PIL import Image
import io
from rembg import remove
import os
import zipfile
import base64
import svgwrite
from io import BytesIO
import sentry_sdk

# Initialize Sentry for error logging
sentry_sdk.init(
    dsn="https://0d1459f593bd0c664f9358987b14a99b@sentry.africantech.dev/8",  # Replace with your actual Sentry DSN
    traces_sample_rate=1.0,  # Adjust this value if needed for performance reasons
    profiles_sample_rate=1.0  # Adjust this value if needed for performance reasons
)


# Helper function for resizing images
def resize_image(image, width, height):
    try:
        return image.resize((width, height))
    except Exception as e:
        st.error(f"Error resizing image: {e}")
        sentry_sdk.capture_exception(e)

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
        st.error(f"Error applying branding: {e}")
        sentry_sdk.capture_exception(e)

# Corrected function for converting image to SVG
def convert_to_svg(image, output_path):
    try:
        # Convert the PIL image to a base64 string
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Create the SVG file and embed the image as a base64 string
        dwg = svgwrite.Drawing(output_path, profile='tiny')
        dwg.add(dwg.image(href=f"data:image/png;base64,{image_base64}", insert=(0, 0), size=(image.width, image.height)))
        dwg.save()
    except Exception as e:
        st.error(f"Error converting image to SVG: {e}")
        sentry_sdk.capture_exception(e)

# Helper function for removing backgrounds
def remove_background(image):
    try:
        return remove(image)
    except Exception as e:
        st.error(f"Error removing background: {e}")
        sentry_sdk.capture_exception(e)

# Helper function to save images into a zip file
def save_images_to_zip(images, zip_buffer):
    try:
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_name, image_data in images:
                zip_file.writestr(file_name, image_data.getvalue())
        zip_buffer.seek(0)
    except Exception as e:
        st.error(f"Error saving images to zip: {e}")
        sentry_sdk.capture_exception(e)

# Main function to handle bulk image processing tasks
def bulk_image_processing():
    try:
        st.title("Bulk Image Processing App")

        # Step 1: Upload multiple images
        uploaded_files = st.file_uploader("Upload multiple images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        if uploaded_files:
            # Display uploaded images
            st.subheader("Uploaded Images")
            for uploaded_file in uploaded_files:
                st.image(uploaded_file, caption=uploaded_file.name)

            # Step 2: Image Resizing
            st.subheader("Resize Images")
            width = st.number_input("Width", min_value=10, max_value=5000, value=800)
            height = st.number_input("Height", min_value=10, max_value=5000, value=600)

            if st.button("Resize Images"):
                resized_images = []
                for uploaded_file in uploaded_files:
                    image = Image.open(uploaded_file)
                    resized_image = resize_image(image, width, height)
                    st.image(resized_image, caption=f"Resized {uploaded_file.name}")
                    img_byte_arr = io.BytesIO()
                    resized_image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    resized_images.append((uploaded_file.name, img_byte_arr))

                zip_buffer = BytesIO()
                save_images_to_zip(resized_images, zip_buffer)
                st.download_button(label="Download Resized Images",
                                   data=zip_buffer,
                                   file_name="resized_images.zip",
                                   mime="application/zip")

            # Step 3: Background Removal
            st.subheader("Remove Backgrounds")
            if st.button("Remove Backgrounds"):
                no_bg_images = []
                for uploaded_file in uploaded_files:
                    image = Image.open(uploaded_file)
                    no_bg_image = remove_background(image)
                    st.image(no_bg_image, caption=f"Background Removed {uploaded_file.name}")
                    img_byte_arr = io.BytesIO()
                    no_bg_image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    no_bg_images.append((uploaded_file.name, img_byte_arr))

                zip_buffer = BytesIO()
                save_images_to_zip(no_bg_images, zip_buffer)
                st.download_button(label="Download Images with Removed Backgrounds",
                                   data=zip_buffer,
                                   file_name="no_bg_images.zip",
                                   mime="application/zip")

            # Step 4: Branding
            st.subheader("Apply Branding")
            branding_file = st.file_uploader("Upload Branding Image (Logo)", type=["png"])
            if branding_file:
                branding_image = Image.open(branding_file)
                st.image(branding_image, caption="Branding Image")

                if st.button("Apply Branding"):
                    branded_images = []
                    for uploaded_file in uploaded_files:
                        image = Image.open(uploaded_file)
                        branded_image = apply_branding(image, branding_image)
                        st.image(branded_image, caption=f"Branded {uploaded_file.name}")
                        img_byte_arr = io.BytesIO()
                        branded_image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        branded_images.append((uploaded_file.name, img_byte_arr))

                    zip_buffer = BytesIO()
                    save_images_to_zip(branded_images, zip_buffer)
                    st.download_button(label="Download Branded Images",
                                       data=zip_buffer,
                                       file_name="branded_images.zip",
                                       mime="application/zip")

            # Step 5: Vectorization (PNG to SVG)
            st.subheader("Vectorize Images (PNG to SVG)")
            if st.button("Convert to SVG"):
                svg_images = []
                for uploaded_file in uploaded_files:
                    image = Image.open(uploaded_file)
                    output_path = f"{uploaded_file.name.split('.')[0]}.svg"
                    convert_to_svg(image, output_path)
                    with open(output_path, "rb") as f:
                        svg_data = f.read()
                        svg_images.append((output_path, BytesIO(svg_data)))

                zip_buffer = BytesIO()
                save_images_to_zip(svg_images, zip_buffer)
                st.download_button(label="Download SVG Images",
                                   data=zip_buffer,
                                   file_name="svg_images.zip",
                                   mime="application/zip")
        else:
            st.warning("Please upload some images to begin processing.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        sentry_sdk.capture_exception(e)

# Run the Streamlit app
if __name__ == "__main__":
    bulk_image_processing()