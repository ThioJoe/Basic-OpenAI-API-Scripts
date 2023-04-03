import openai
import json

model = "gpt-4"
systemPrompt = "You are a helpful assistant."

# ----------------------------------------------------------------------------------

# Load API key from key.txt file
def load_api_key(filename="key.txt"):
    try:
        with open(filename, "r") as key_file:
            for line in key_file:
                stripped_line = line.strip()
                if not stripped_line.startswith('#') and stripped_line != '':
                    api_key = stripped_line
                    break
        return api_key
    except FileNotFoundError:
        print("\nAPI key file not found. Please create a file named 'key.txt' in the same directory as this script and paste your API key in it.\n")
        exit()

openai.api_key = load_api_key()

def send_and_receive_message(userMessage, messagesTemp, temperature=0.5):
    messagesTemp.append({"role": "user", "content": userMessage})

    chatResponse = openai.ChatCompletion.create(
        model=model,
        messages=messagesTemp,
        temperature=temperature
        )
    
    chatResponseMessage = chatResponse.choices[0].message.content
    chatResponseRole = chatResponse.choices[0].message.role

    print("\n" + chatResponseMessage)

    messagesTemp.append({"role": chatResponseRole, "content": chatResponseMessage})

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
    with open(filename, "w", encoding="utf-8") as outfile:
        json.dump(messages, outfile, ensure_ascii=False, indent=4)
    print(f"\nConversation history saved to {filename}.")
    return ""

def load_conversation_history():
    filename = input("\nEnter the file name to load the conversation: ")
    global messages
    with open(filename, "r", encoding="utf-8") as infile:
        messages = json.load(infile)
    print(f"\nConversation history loaded from {filename}.")
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

messages = [{"role": "system", "content": systemPrompt}]
temperature = 0.5

# Print list of special commands and description
print("---------------------------------------------")
print("\nBegin the chat by typing your message and hitting Enter. Here are some special commands you can use:\n")
print("  file:   Send the contents of a text file as your message. It will ask you for the file path of the file.")
print("  clear:  Clear the conversation history.")
print("  save:   Save the conversation history to a file.")
print("  load:   Load the conversation history from a file.")
print("  switch: Switch the model.")
print("  temp:   Set the temperature.")
print("  exit:   Exit the script.\n")


while True:
    userEnteredPrompt = input("\n >>>    ")
    userEnteredPrompt = check_special_input(userEnteredPrompt)
    if userEnteredPrompt:
        messages = send_and_receive_message(userEnteredPrompt, messages, temperature)
