from openai import OpenAI
import json
import tkinter as tk
import datetime
import os
from tkinter import scrolledtext
import glob

# Some Models:
# gpt-4
# gpt-3.5-turbo-16k

model = "gpt-4"
systemPrompt = "You are a helpful assistant."

# Create 'Chat Logs' directory if it does not exist
if not os.path.exists('Chat Logs'):
    os.makedirs('Chat Logs')
    
# Create 'Saved Chats' directory if it does not exist
if not os.path.exists('Saved Chats'):
    os.makedirs('Saved Chats')    

# ----------------------------------------------------------------------------------

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

client = OpenAI(api_key=load_api_key())  # Retrieves key from key.txt file  

# Generate the filename only once when the script starts
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file_path = os.path.join('Chat Logs', f'log_{timestamp}.txt')

def send_and_receive_message(userMessage, messagesTemp, temperature=0.5):
    # Prepare to send request along with context by appending user message to previous conversation
    messagesTemp.append({"role": "user", "content": userMessage})

    # Log the user's message before the API call
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        indented_user_message = f"{messagesTemp[-1]['content']}".replace('\n', '\n    ')
        log_file.write(f"{messagesTemp[-1]['role'].capitalize()}:\n\n    {indented_user_message}\n\n")  # Extra '\n' for blank line

    # Call the OpenAI API
    chatResponse = client.chat.completions.create(
        model=model,
        messages=messagesTemp,
        temperature=temperature
    )
    chatResponseData = chatResponse.choices[0].model_dump()["message"]
    chatResponseMessage = chatResponseData["content"]
    chatResponseRole = chatResponseData["role"]

    print("\n" + chatResponseMessage)

    # Append chatbot response to full conversation dictionary
    messagesTemp.append({"role": chatResponseRole, "content": chatResponseMessage})

    # Write the assistant's response to the log file
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        indented_response = f"{messagesTemp[-1]['content']}".replace('\n', '\n    ')
        log_file.write(f"{messagesTemp[-1]['role'].capitalize()}:\n\n    {indented_response}\n\n")  # Indent assistant entries

    return messagesTemp

def check_special_input(text):
    if text == "file":
        text = get_text_from_file()
    elif text == "clear":
        text = clear_conversation_history()
    elif text == "save":
        text = save_conversation_history()
    elif text == "load":
        text = load_conversation_history()
    elif text == "switch":
        text = switch_model()
    elif text == "temp":
        text = set_temperature()
    elif text == "box":
        text = get_multiline_input()
    elif text == "exit":
        exit_script()
    return text

def get_text_from_file():
    path = input("\nPath to the text file contents to send: ")
    path = path.strip('"')
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return text

def clear_conversation_history():
    global messages
    messages = [{"role": "system", "content": systemPrompt}]
    print("\nConversation history cleared.")
    return ""

def save_conversation_history():
    filename = input("\nEnter the file name to save the conversation: ")
    # Check if the filename has an extension. If not, add '.txt'
    filename_without_ext, file_extension = os.path.splitext(filename)
    if file_extension == '':
        filename += '.txt'
    save_path = os.path.join('Saved Chats', filename)
    with open(save_path, "w", encoding="utf-8") as outfile:
        json.dump(messages, outfile, ensure_ascii=False, indent=4)
    print(f"\nConversation history saved to {save_path}.")
    return ""

def load_conversation_history():
    filename = input("\nEnter the file name to load the conversation: ")
    filename_without_ext, file_extension = os.path.splitext(filename)
    load_path = os.path.join('Saved Chats', filename)

    # If no extension is provided, try to load a file with no extension
    if file_extension == '':
        if not os.path.exists(load_path):
            # If no such file, try to load a file with a .txt extension
            try_txt_path = os.path.join('Saved Chats', filename + '.txt')
            if os.path.exists(try_txt_path):
                load_path = try_txt_path
            # If the file is still not found, look for any file with that base name
            else:
                potential_files = glob.glob(os.path.join('Saved Chats', filename + '.*'))
                if len(potential_files) == 1:
                    load_path = potential_files[0]
                elif len(potential_files) > 1:
                    print(f"\nERROR: Multiple files with the name '{filename}' found with different extensions. Please specify the full exact filename, including extension.")
                    return ""

    global messages
    try:
        with open(load_path, "r", encoding="utf-8") as infile:
            messages = json.load(infile)
        print(f"\nConversation history loaded from {load_path}.")
    except FileNotFoundError:
        print(f"\nERROR: File '{filename}' not found. Please make sure the file exists in the 'Saved Chats' folder.")
    except json.decoder.JSONDecodeError:
        print(f"\nERROR: File '{filename}' is not a valid JSON file. Did you try to load a file that was not saved using the 'save' command? Note: The automatically generated log files cannot be loaded.")
    return ""

def switch_model():
    global model
    new_model = input("\nEnter the new model name (e.g., 'gpt-4', 'gpt-3', etc.): ")
    model = new_model
    print(f"\nModel switched to {model}.")
    return ""

def set_temperature():
    global temperature
    temp = float(input("\nEnter a temperature value between 0 and 1 (default is 0.5): "))
    temperature = temp
    print(f"\nTemperature set to {temperature}.")
    return ""

def exit_script():
    print("\nExiting the script. Goodbye!")
    exit()


def get_multiline_input():
    def submit_text():
        nonlocal user_input
        user_input = text_box.get("1.0", tk.END)
        root.quit()

    user_input = ""
    root = tk.Tk()
    root.title("Multi-line Text Input")
    root.attributes('-topmost', True)

    # Set the initial window size
    root.geometry('450x300')

    # Create a scrolled text widget
    text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    text_box.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

    # Create a submit button
    submit_button = tk.Button(root, text="Submit", command=submit_text)
    submit_button.grid(row=1, column=0, pady=5)

    # Configure the grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()
    root.destroy()

    return user_input.strip()

messages = [{"role": "system", "content": systemPrompt}]
temperature = 0.5

# Print list of special commands and description
print("---------------------------------------------")
print("\nBegin the chat by typing your message and hitting Enter. Here are some special commands you can use:\n")
print("  file:   Send the contents of a text file as your message. It will ask you for the file path of the file.")
print("  box:    Send the contents of a multi-line text box as your message. It will open a new window with a text box.")
print("  clear:  Clear the conversation history.")
print("  save:   Save the conversation history to a file in 'Saved Chats' folder.")
print("  load:   Load the conversation history from a file in 'Saved Chats' folder.")
print("  switch: Switch the model.")
print("  temp:   Set the temperature.")
print("  exit:   Exit the script.\n")


while True:
    userEnteredPrompt = input("\n >>>    ")
    userEnteredPrompt = check_special_input(userEnteredPrompt)
    if userEnteredPrompt:
        print("----------------------------------------------------------------------------------------------------")
        messages = send_and_receive_message(userEnteredPrompt, messages, temperature)
