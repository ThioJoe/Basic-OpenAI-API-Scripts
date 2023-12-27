#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======================================================================================================================================
# ========================================================= USER SETTINGS ==============================================================
# ======================================================================================================================================

# 4000 characters max prompt length for DALL-E 3, 1000 for DALL-E 2
prompt = "Incredibly cute creature drawing. Round and spherical, very fluffy. Colored pencil drawing."

# Number of images to generate  |  (Take note of your rate limits: https://platform.openai.com/docs/guides/rate-limits/usage-tiers )
image_count = 4

# DALLE-2 or DALLE-3
dalle_version = 3       # 2 or 3

# DALLE-3 Options:
dalle3_size = "W"       # S/square | W/wide | T/tall -- (1024x1024, 1792x1024, 1024x1792)
quality = "standard"    # Standard / HD
style = "vivid"         # "vivid" or "natural"

# DALLE-2 Options:
dalle2_size = "L"  # S/small | M/medium | L/large -- (256x256, 512x512, 1024x1024)

output_dir = 'Image Outputs'

# ======================================================================================================================================
# ======================================================================================================================================
# ======================================================================================================================================

import os
from io import BytesIO
from datetime import datetime
import base64
from PIL import Image, ImageTk
import tkinter as tk
import asyncio
import aiohttp
from openai import OpenAI
import math
#import requests #If downloading from URL, not currently implemented

# --------------------------------------------------- SETTINGS VALIDATION ---------------------------------------------------------------

# Valid settings for each setting
valid_dalle_versions = [2, 3]
valid_qualities = ["standard", "hd"]
valid_styles = ["vivid", "natural"]
valid_dalle3_sizes = ["1024x1024", "1792x1024", "1024x1792", "square", "wide", "tall", "s", "w", "t"]
valid_dalle2_sizes = ["256x256", "512x512", "1024x1024", "small", "medium", "large", "s", "m", "l"]


# Validate user settings
if dalle_version not in valid_dalle_versions:
    print(f"\nERROR - Invalid DALLE version: {dalle_version}. Please choose either 2 or 3.")
    exit()
    
if dalle_version == 3:
    if quality.lower() not in valid_qualities:
        print(f"\nERROR - Invalid quality: {quality}. Please choose either 'standard' or 'hd'.")
        exit()
    if style.lower() not in valid_styles:
        print(f"\nERROR - Invalid style: {style}. Please choose either 'vivid' or 'natural'.")
        exit()
    if dalle3_size.lower() not in valid_dalle3_sizes:
        print(f"\nERROR - Invalid size for DALLE-3: {dalle3_size}. Valid values are: {valid_dalle3_sizes}")
        exit()
        
if dalle_version == 2:
    if dalle2_size.lower() not in valid_dalle2_sizes:
        print(f"\nERROR - Invalid size for DALLE-2: {dalle2_size}. Valid values are: {valid_dalle2_sizes}")
        exit()
    # if image_count > 10:
    #     print(f"\nERROR - Invalid image_count value: {image_count}. DALLE-2 only supports up to 10 images per request.")
    #     exit()

# Define image parameters based on user settings
if dalle_version == 3:
    model = 'dall-e-3'
    # Create list of batches of length image_count with 1 image per batch
    images_per_batch_list = [1] * image_count
    
    # Define Size
    if dalle3_size.lower() in ["1024x1024", "square", "s"]:
        size = "1024x1024"
    elif dalle3_size.lower() in ["1792x1024", "wide", "w"]:
        size = "1792x1024"
    elif dalle3_size.lower() in ["1024x1792", "tall", "t"]:
        size = "1024x1792"
    
elif dalle_version == 2:
    model = 'dall-e-2'
    
    # Calculate list of batches required to generate image_count images, max 10 per batch, ensure leftover images are in their own batch
    images_per_batch_list = [10] * (image_count // 10)
    if image_count % 10 != 0:
        images_per_batch_list.append(image_count % 10)
       
    # Define Size
    if dalle2_size.lower() in ["256x256", "small", "s"]:
        size = "256x256"
    elif dalle2_size.lower() in ["512x512", "medium", "m"]:
        size = "512x512"
    elif dalle2_size.lower() in ["1024x1024", "large", "l"]:
        size = "1024x1024"
    
# Construct image_params dictionary based on user settings
image_params = {
"model": model,  # dall-e-3 or dall-e-2
"quality": quality,  # Standard / HD - (DALLE-3 Only)
"size": size,  # DALLE3 Options: 1024x1024 | 1792x1024 | 1024x1792 -- DALLE2 Options: 256x256 | 512x512 | 1024x1024
"style": style,  # "vivid" or "natural" - (DALLE-3 Only)
# ------- Don't Change Below --------
"prompt": prompt,     
"user": "User",     # Can add customer identifier to for abuse monitoring
"response_format": "b64_json",  # "url" or "b64_json"
"n": 1,  # DALLE3 must be 1. DALLE2 up to 10. Update this value to change number of images per request
}

# --------------------------------------------------------------------------------------------------------------------------------------

# Validate API Key
def validate_api_key(api_key):
    # Check if string begins with 'sk-'
    if not api_key.lower().startswith('sk-'):
        if api_key == "":
            print("\nERROR - No API key found in key.txt. Please paste your API key in key.txt and try again.")
        else:
            print("\nERROR - Invalid API key found in key.txt. Please check your API key and try again.")
        exit()
    else:
        return api_key

# Load API key from key.txt file
def load_api_key(filename="key.txt"):
    api_key = ""
    try:
        with open(filename, "r", encoding='utf-8') as key_file:
            for line in key_file:
                stripped_line = line.strip()
                if not stripped_line.startswith('#') and stripped_line != '':
                    api_key = stripped_line
                    break
        api_key = validate_api_key(api_key)
        return api_key
    except FileNotFoundError:
        print("\nAPI key file not found. Please create a file named 'key.txt' in the same directory as this script and paste your API key in it.\n")
        exit()

   
def set_filename_base(model=None, imageParams=None):
    # Can pass in either the model name directly or the imageParams dictionary used in API request
    if imageParams:
        model = imageParams["model"]
        
    if model.lower() == "dall-e-3":
        base_img_filename = "DALLE3"
    elif model.lower() == "dall-e-2":
        base_img_filename = "DALLE2"
    else:
        base_img_filename = "Image"
        
    return base_img_filename
    
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------

async def main():    
    client = OpenAI(api_key=load_api_key())  # Retrieves key from key.txt file  
   
    async def generate_images_batch(client, image_params, base_img_filename, images_in_batch, start_index=0):
        # Update image_params with number of images to generate this batch
        image_params["n"] = images_in_batch
        try:
            # Make an API request for images
            images_response = await asyncio.to_thread(client.images.generate, **image_params)
        except Exception as e:
            print(f"Error occurred during generation of image(s): {e}")
            return None
        
        # Create a unique filename for this image
        images_dt = datetime.utcfromtimestamp(images_response.created)
        
        batch_image_dicts_list = []
        
        i = start_index
        # Process the response
        for image_data in images_response.data:
            img_filename = images_dt.strftime(f'{base_img_filename}-%Y%m%d_%H%M%S_{i}')
            # Extract either the base64 image data or the image URL
            image_obj = image_data.model_dump()["b64_json"]
            
            if image_obj:
                # Decode any returned base64 image data
                image_obj = Image.open(BytesIO(base64.b64decode(image_obj)))
                image_path = os.path.join(output_dir, f"{img_filename}.png")
                image_obj.save(image_path)
                print(f"{image_path} was saved")
                
                revised_prompt = image_data.model_dump()["revised_prompt"]
                if not revised_prompt:
                    revised_prompt = "N/A"
                
                # Create dictionary with image_obj and revised_prompt to return
                generated_image = {"image": image_obj, "revised_prompt": revised_prompt, "file_name": f"{img_filename}.png", "image_params": image_params}
                batch_image_dicts_list.append(generated_image)
                i = i + 1
        
        return batch_image_dicts_list
    
    print("\nGenerating images...")
    base_img_filename=set_filename_base(imageParams=image_params)
    
    # Check if 'output' folder exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    generated_image_dicts_batches_list = []
    tasks = []
    index = 0
    for images_in_batch in images_per_batch_list:
        # Call function that generates the images
        task = generate_images_batch(client, image_params, base_img_filename, images_in_batch, start_index=index)
        if task is not None: # In case some of the images fail to generate, we don't want to append None to the list
            index = index + images_in_batch
            tasks.append(task)

    generated_image_dicts_batches_list = await asyncio.gather(*tasks) # Gives a list of lists of dictionaries
    
    flattened_generated_image_dicts_list = []
    image_objects_to_display = []
    
    # Flatten the nested lists of dictionaries into a single list of dictionaries. Get image objects and put into list to display later
    for image_dict_list in generated_image_dicts_batches_list:
        for image_dict in image_dict_list:
            if image_dict is not None:
                flattened_generated_image_dicts_list.append(image_dict)
                image_objects_to_display.append(image_dict["image"])
    
    # Open a text file to save the revised prompts. It will open within the Image Outputs folder in append only mode. It appends the revised prompt to the file along with the file name
    with open(os.path.join(output_dir, "Image_Log.txt"), "a") as log_file:
        for image_dict in flattened_generated_image_dicts_list:
            if image_dict is not None:
                # If using DALLE-2, adjust not-applicable parameters
                if dalle_version == 2:
                    image_dict["image_params"]["quality"] = "N/A"
                    image_dict["image_params"]["style"] = "N/A"
                log_file.write(
                                f"{image_dict['file_name']}: \n"
                                f"\t Quality:\t\t\t\t{image_dict['image_params']['quality']}\n"
                                f"\t Style:\t\t\t\t\t{image_dict['image_params']['style']}\n"
                                f"\t Revised Prompt:\t\t{image_dict['revised_prompt']}\n"
                                f"\t User-Written Prompt:\t{image_params['prompt']}\n\n"
                                )

# --------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- Image  Preview Window Code -----------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
    if not image_objects_to_display:
        print("\nNo images were generated.")
        exit()

    # Calculates how many rows/columns are needed to display images in a most square fashion
    def calculate_grid_dimensions(num_images):
        grid_size = math.ceil(math.sqrt(num_images))
        
        # For a square grid or when there are fewer images than the grid size
        if num_images <= grid_size * (grid_size - 1):
            # Use one less row or column
            rows = min(num_images, grid_size - 1)
            columns = math.ceil(num_images / rows)
        else:
            # Use a square grid
            rows = columns = grid_size
            
        if aspect_ratio > 1.5:
            # Stack images horizontally first
            rows, columns = columns, rows

        return rows, columns

    def resize_images(window, original_image_objects, labels, last_resize_dim):
        window_width = window.winfo_width()
        window_height = window.winfo_height()

        # Check if the change in window size exceeds the threshold, then resize images if so
        if (abs(window_width - last_resize_dim[0]) > resize_threshold or abs(window_height - last_resize_dim[1]) > resize_threshold):
            last_resize_dim[0] = window_width
            last_resize_dim[1] = window_height
            
            # Calculate the size of the grid cell
            cell_width = window_width // num_columns
            cell_height = window_height // num_rows

            def resize_aspect_ratio(img, max_width, max_height):
                original_width, original_height = img.size
                ratio = min(max_width/original_width, max_height/original_height)
                new_size = (int(original_width * ratio), int(original_height * ratio))
                return img.resize(new_size, Image.Resampling.BILINEAR)

            # Resize and update each image to fit its cell
            for original_img, label in zip(original_image_objects, labels):
                resized_img = resize_aspect_ratio(original_img, cell_width, cell_height)
                tk_image = ImageTk.PhotoImage(resized_img)
                label.configure(image=tk_image)
                label.image = tk_image  # Keep a reference to avoid garbage collection

    # Get images aspect ratio to decide whether to stack images horizontally or vertically first
    img_width = image_objects_to_display[0].width
    img_height = image_objects_to_display[0].height
    aspect_ratio = img_width / img_height
    desired_initial_size = 300

    # Resize threshold in pixels, minimum change in window size to trigger resizing of images
    resize_threshold = 5  # Setting this too low may cause laggy window
  
    # Calculate grid size (rows and columns)
    grid_size = math.ceil(math.sqrt(len(image_objects_to_display)))

    # Create a single tkinter window
    window = tk.Tk()
    window.title("Images Preview")

    num_rows, num_columns = calculate_grid_dimensions(len(image_objects_to_display))

    # Calcualte scale multiplier to get smallest side to fit desired initial size
    scale_multiplier = desired_initial_size / min(img_width, img_height)

    # Set initial window size to fit all images
    initial_window_width = int(img_width * num_columns * scale_multiplier)
    initial_window_height = int(img_height * num_rows * scale_multiplier)
    window.geometry(f"{initial_window_width}x{initial_window_height}")

    labels = []
    original_image_objects = [img.copy() for img in image_objects_to_display]  # Store original images for resizing

    for i, img in enumerate(image_objects_to_display):
        # Convert PIL Image object to PhotoImage object
        tk_image = ImageTk.PhotoImage(img)
        
        # Determine row and column for this image
        if aspect_ratio > 1.5:
            # Stack images horizontally first
            row = i % grid_size
            col = i // grid_size
        else:
            row = i // grid_size
            col = i % grid_size

        # Create a 'label' to be able to display image within it
        label = tk.Label(window, image=tk_image, borderwidth=2, relief="groove")
        label.image = tk_image  # Keep a reference to avoid garbage collection
        label.grid(row=row, column=col, sticky="nw")
        labels.append(label)

    # Configure grid weights to allow dynamic resizing
    for r in range(num_columns):
        window.grid_rowconfigure(r, weight=0) # Setting weight to 0 keeps images pinned to top left
    for c in range(num_rows):
        window.grid_columnconfigure(c, weight=0) # Setting weight to 0 keeps images pinned to top left

    # Initialize last_resize_dim
    last_resize_dim = [window.winfo_width(), window.winfo_height()]

    # Bind resize event
    window.bind('<Configure>', lambda event: resize_images(window, original_image_objects, labels, last_resize_dim))

    # Run the tkinter main loop - this will display all images in a single window
    print("\nFinished - Displaying images in window (it may be minimized).")
    window.mainloop()
            

# --------------------------------------------------------------------------------------------------------------------------------------   
            
# Run the main function with asyncio
if __name__ == "__main__":
    asyncio.run(main())