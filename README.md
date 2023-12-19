# Basic-GPT-API
A basic script for interacting with the GPT-4 API and chatting with it via python.

## How to Use:
1. Make sure any required packages are installed. You can use `pip install -r requirements.txt`
   - Currently the only required package is `openai`
2. Add your OpenAI API key to `key.txt`
3. Run `chat.py`

## Screenshot:
<img width="817" alt="image" src="https://github.com/ThioJoe/Basic-GPT-API/assets/12518330/a2d5ba52-6377-4dc2-b0bb-60a73681c992">

## DALLE-3 Image Generation Script
- Open `Dalle3.py` and edit any settings you want under "User Settings" near the top. Including the prompt and number of images to generate at once.
- After all images are generated and returned, a window with the images will be shown
- Automatically saves the images into an output folder, and records the "revised prompts" for each image (the prompt actually used, that was based on the user-provided prompt)
