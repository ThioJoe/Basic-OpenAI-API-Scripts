#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------
# Requirements:
# pip install --upgrade openai
# pip install pillow
# pip install aiohttp

# ======================================================================================================================================
# ========================================================= USER SETTINGS ==============================================================
# ======================================================================================================================================

# Number of images to generate
# Take note of your rate limits: https://platform.openai.com/docs/guides/rate-limits/usage-tiers
num_requests = 2

# 4000 characters max prompt length for DALL-E 3, 1000 for DALL-E 2
prompt = "Incredibly cute creature drawing. Round and spherical, very fluffy. Colored pencil drawing."

image_params = {
"model": "dall-e-3",  # dall-e-3 or dall-e-2
"quality": "standard",  # Standard / HD - (DALLE-3 Only)
"size": "1024x1024",  # 1792x1024 or 1024x1792 for DALL-E 3
"style": "vivid",  # "vivid" or "natural" - (DALLE-3 Only)
# ------- Don't Change Below --------
"prompt": prompt,     
"user": "User",     # Can add customer identifier to for abuse monitoring
"response_format": "b64_json",  # "url" or "b64_json"
"n": 1,               # DALLE3 must be 1. DALLE2 up to 10
}

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

# Load API key from key.txt file
def load_api_key(filename="key.txt"):
    try:
        with open(filename, "r", encoding='utf-8') as key_file:
            for line in key_file:
                stripped_line = line.strip()
                if not stripped_line.startswith('#') and stripped_line != '':
                    api_key = stripped_line
                    break
        return api_key
    except FileNotFoundError:
        print("\nAPI key file not found. Please create a file named 'key.txt' in the same directory as this script and paste your API key in it.\n")
        exit()

async def fetch_image(session, url, img_filename, i):
    async with session.get(url) as response:
        if response.status != 200:
            print(f"Failed to download image from {url}. Status: {response.status}")
            return None
        content = await response.read()
        image = Image.open(BytesIO(content))
        image.save(f"{img_filename}_{i}.png")
        print(f"{img_filename}_{i}.png was saved")
        return image
    
async def generate_single_image(client, image_params, img_filename, index):
    try:
        images_response = await asyncio.to_thread(client.images.generate, **image_params)
        image_url_list = [image.model_dump()["url"] for image in images_response.data]
        image_objects = await download_images(image_url_list, f"{img_filename}_{index}")
        return image_objects
    except Exception as e:
        print(f"Error: {e}")
        return []    

async def download_images(image_urls, img_filename):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image(session, url, img_filename, i) for i, url in enumerate(image_urls)]
        return await asyncio.gather(*tasks)
    
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
  
    async def generate_single_image(client, image_params, base_img_filename, index):
        try:
            
            # Make an API request for a single image
            images_response = await asyncio.to_thread(client.images.generate, **image_params)

            # Create a unique filename for this image
            images_dt = datetime.utcfromtimestamp(images_response.created)
            img_filename = images_dt.strftime(f'{base_img_filename}-%Y%m%d_%H%M%S_{index}')

            # Process the response
            image_data = images_response.data[0]

            # Extract either the base64 image data or the image URL
            image_obj = image_data.model_dump()["b64_json"]
            image_url = image_data.model_dump()["url"]

            # Extract Additional Data
            revised_prompt = image_data.model_dump()["revised_prompt"]
            
            if image_obj:
                # Decode any returned base64 image data
                image_obj = Image.open(BytesIO(base64.b64decode(image_obj)))  # Append the Image object to the list
            elif image_url:
                # Download any image from URL
                async with aiohttp.ClientSession() as session:
                    image_obj = await fetch_image(session, image_url, output_dir, index)
            else:
                print(f"No image URL or Image found for request {index}.")
                return None

            # Check if 'output' folder exists, if not create it
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if image_obj is not None:
                image_path = os.path.join(output_dir, f"{img_filename}.png")
                image_obj.save(image_path)
                print(f"{image_path} was saved")
                
                # Create dictionary with image_obj and revised_prompt to return
                generated_image = {"image": image_obj, "revised_prompt": revised_prompt, "file_name": f"{img_filename}.png", "image_params": image_params}
                return generated_image
            
            else:
                return None

        except Exception as e:
            print(f"Error occurred during generation of image {index}: {e}")
            return None

    generated_image_dicts_list = []
    tasks = []
    base_img_filename=set_filename_base(imageParams=image_params)
    
    for i in range(num_requests):
        task = generate_single_image(client, image_params, base_img_filename, index=i)
        if task is not None: # In case some of the images fail to generate, we don't want to append None to the list
            tasks.append(task)

    generated_image_dicts_list = await asyncio.gather(*tasks)
    
    # Get the image objects from the dictionaries and put into image_objects list
    image_objects = []
    for image_dict in generated_image_dicts_list:
        if image_dict is not None:
            image_objects.append(image_dict["image"])
    
    # Open a text file to save the revised prompts. It will open within the Image Outputs folder in append only mode. It appends the revised prompt to the file along with the file name
    with open(os.path.join(output_dir, "Image_Log.txt"), "a") as log_file:
        for image_dict in generated_image_dicts_list:
            log_file.write(
                                f"{image_dict['file_name']}: \n"
                                f"\t Quality:\t\t\t\t{image_dict['image_params']['quality']}\n"
                                f"\t Style:\t\t\t\t\t{image_dict['image_params']['style']}\n"
                                f"\t User-Written Prompt:\t{image_params['prompt']}\n"
                                f"\t Revised Prompt:\t\t{image_dict['revised_prompt']}\n\n"
                                )

    # Display list of PIL Image objects in a tkinter window
    if image_objects:
        
        # Calculate grid size (rows and columns)
        grid_size = math.ceil(math.sqrt(len(image_objects)))
        
        # Create a single tkinter window
        window = tk.Tk()
        window.title("Images Preview")
        
        # Set the window as topmost initially
        window.attributes('-topmost', True)
        window.after_idle(window.attributes, '-topmost', False)

        for i, img in enumerate(image_objects):
            # Resize image
            if img.width > 512 or img.height > 512:
                img.thumbnail((300, 300))  # Resize but keep aspect ratio

            # Convert PIL Image object to PhotoImage object
            tk_image = ImageTk.PhotoImage(img)
            
            # Determine row and column for this image
            row = i // grid_size
            col = i % grid_size

            # Create a 'lablel' to be able to display image within it
            label = tk.Label(window, image=tk_image)
            label.image = tk_image  # Keep a reference to avoid garbage collection
            label.grid(row=row, column=col)

        # Run the tkinter main loop - this will display all images in a single window
        print("\nFinished - Displaying images in window (it may be minimized).")
        window.mainloop()
            

# --------------------------------------------------------------------------------------------------------------------------------------   
            
# Run the main function with asyncio
if __name__ == "__main__":
    asyncio.run(main())