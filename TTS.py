#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======================================================================================================================================
# ========================================================= USER SETTINGS ==============================================================
# ======================================================================================================================================

# Speech file base name - numbers will be appended to this for each file added
speech_file_base_name = "speech"
outputFolder = "TTS-Outputs"

model = "tts-1-hd" # "tts-1" or "tts-1-hd"
voice = "alloy" # alloy, echo, fable, onyx, nova, shimmer
text = "This is what I'm going to say!"

# ======================================================================================================================================
# ======================================================================================================================================
# ======================================================================================================================================

from openai import OpenAI
import os

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

# This creates the authenticated OpenAI client object that we can use to send requests
client = OpenAI(api_key=load_api_key())  # Retrieves key from key.txt file  

# This sends the API Request
response = client.audio.speech.create(
  model=model,
  voice=voice,
  input=text
)

# Create outputFolder
if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)

# Determine file name by finding the next available number out of files in the outputFolder. Starting with no number then starting at 2
file_name = f"{speech_file_base_name}.mp3"
file_number = 2
while os.path.exists(os.path.join(outputFolder, file_name)):
    file_name = f"{speech_file_base_name}_{file_number}.mp3"
    file_number += 1
    
# Save the audio to a file
filePath = os.path.join(outputFolder, file_name)
response.stream_to_file(filePath)