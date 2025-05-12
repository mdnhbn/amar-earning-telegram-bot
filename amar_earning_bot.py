import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import json
import os # os import করা হয়েছে

# --- Configuration ---
# API টোকেন এখন এনভায়রনমেন্ট ভেরিয়েবল থেকে নেওয়া হবে
API_TOKEN = os.environ.get('7739431310:AAFrvR3PaMDo8AizVHHDTZzgcipgi03oSjQ')
# DATA_FILE এর পাথ Render.com এর ডিস্ক অনুযায়ী সেট করতে হবে
# নিচের পাথটি একটি উদাহরণ, Render এ ডিস্ক তৈরি করার সময় সঠিক পাথটি দিতে হবে
DATA_DIR = "/mnt/data/amar_earning_bot_data" # Render এ ডিস্ক মাউন্ট পাথ অনুযায়ী
DATA_FILE = os.path.join(DATA_DIR, "keywords.json")

# --- Initialize Bot ---
# Check if API_TOKEN is set
if API_TOKEN is None:
    print("CRITICAL ERROR: TELEGRAM_API_TOKEN environment variable not found!")
    # You might want to exit or raise an exception here depending on your preference
    # For now, let's try to proceed but it will likely fail later
    # raise ValueError("TELEGRAM_API_TOKEN not set!")
    API_TOKEN = "YOUR_FALLBACK_TOKEN_IF_ANY" # Or handle the error appropriately

bot = telebot.TeleBot(API_TOKEN)

# --- Ensure Data Directory Exists ---
# This should be done before attempting to load/save keywords
if API_TOKEN != "YOUR_FALLBACK_TOKEN_IF_ANY": # Only proceed if token is likely valid
    try:
        os.makedirs(DATA_DIR, exist_ok=True) # exist_ok=True prevents error if dir exists
        print(f"DEBUG: Data directory checked/created: {DATA_DIR}")
    except OSError as e:
        print(f"CRITICAL ERROR: Could not create data directory {DATA_DIR}: {e}")
        # Handle this error - maybe the bot can't function without storage

# --- Helper Functions for Data Persistence ---
def load_keywords():
    """Loads keywords from the JSON file."""
    print(f"DEBUG: Attempting to load keywords from {DATA_FILE}...")
    if not os.path.exists(DATA_DIR):
         print(f"Warning: Data directory {DATA_DIR} does not exist. Cannot load keywords.")
         return {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    print(f"Info: {DATA_FILE} is empty. Starting with an empty keyword list.")
                    return {}
                keywords_data = json.loads(content)
                print(f"DEBUG: Successfully loaded keywords: {list(keywords_data.keys())}") # Print only keys for brevity
                return keywords_data
        except json.JSONDecodeError:
            print(f"Warning: {DATA_FILE} is corrupted. Starting with an empty keyword list.")
            return {}
        except Exception as e:
            print(f"Error loading keywords: {e}")
            return {}
    else:
        print(f"Info: {DATA_FILE} does not exist. Starting with an empty keyword list.")
        return {}

def save_keywords(keywords_data):
    """Saves keywords to the JSON file."""
    if not os.path.exists(DATA_DIR):
         print(f"Warning: Data directory {DATA_DIR} does not exist. Cannot save keywords.")
         return
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(keywords_data, f, indent=4, ensure_ascii=False)
        print(f"DEBUG: Keywords saved to {DATA_FILE}. Count: {len(keywords_data)}") # Print count for brevity
    except Exception as e:
        print(f"Error saving keywords: {e}")

# Load keywords at startup
keywords = load_keywords()

# --- Set Bot Commands for the Menu ---
def set_bot_commands():
    # Only set commands if the token seems valid
    if API_TOKEN != "YOUR_FALLBACK_TOKEN_IF_ANY":
        commands = [
            BotCommand("/start", "🚀 Start the bot and see options"),
            BotCommand("/list", "📄 View all saved keywords"),
            BotCommand("/remove", "🗑️ Delete a keyword"),
            BotCommand("/settings", "⚙️ Admin settings (placeholder)")
        ]
        try:
            bot.set_my_commands(commands)
            print("Bot commands updated successfully.")
        except Exception as e:
            print(f"Error setting bot commands: {e}")
    else:
        print("Skipping setting bot commands due to missing API token.")


# --- Bot Handlers --- (Handlers remain the same as the last working version)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(f"DEBUG: Received /start command from chat ID: {message.chat.id}")
    welcome_text = (
        "Welcome to the AmarEarning_bot!\n"
        "I can help you auto-reply in your Telegram group using keywords.\n\n"
        "➤ Join our Telegram Group: https://t.me/eiminig\n"
        "➤ Subscribe to our YouTube Channel: https://www.youtube.com/@Expatriate_Life1\n\n"
        "Tap \"Start\" below to add a keyword + link."
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Start", callback_data="add_keyword_start"))
    try:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_welcome: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "add_keyword_start")
def handle_add_keyword_start(call):
    print(f"DEBUG: Received 'add_keyword_start' callback from chat ID: {call.message.chat.id if call.message else 'Unknown'}")
    try:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "Please type your keyword:")
        bot.register_next_step_handler(msg, process_keyword_step)
    except Exception as e:
        print(f"Error in handle_add_keyword_start callback: {e}")
        if call.message:
            try:
                bot.send_message(call.message.chat.id, "An error occurred. Please try again.")
            except Exception as e2:
                 print(f"Error sending error message in handle_add_keyword_start: {e2}")


def process_keyword_step(message):
    print(f"DEBUG: process_keyword_step, received keyword: '{message.text}' from chat ID: {message.chat.id}")
    try:
        keyword_text = message.text.strip()
        if not keyword_text:
            bot.reply_to(message, "Keyword cannot be empty. Please try again or type /start to begin anew.")
            return
        if keyword_text.startswith('/'):
            bot.reply_to(message, "Keywords cannot start with '/'. Please choose a different keyword.")
            return
        chat_id = message.chat.id
        msg = bot.send_message(chat_id, "Now send the link or message you want to associate with this keyword:")
        bot.register_next_step_handler(msg, process_link_step, keyword_text)
    except Exception as e:
        print(f"Error in process_keyword_step: {e}")
        try:
            bot.reply_to(message, "An error occurred processing the keyword. Please try again.")
        except Exception as e2:
            print(f"Error sending error message in process_keyword_step: {e2}")


def process_link_step(message, keyword_text):
    print(f"DEBUG: process_link_step, for keyword '{keyword_text}', received link/message: '{message.text}' from chat ID: {message.chat.id}")
    try:
        link_or_message_text = message.text.strip()
        if not link_or_message_text:
            bot.reply_to(message, "The link/message cannot be empty. Please try again or type /start to begin anew.")
            return
        keywords[keyword_text] = link_or_message_text
        save_keywords(keywords)
        bot.send_message(message.chat.id, f"✅ Your keyword '{keyword_text}' has been saved successfully.")
    except Exception as e:
        print(f"Error in process_link_step: {e}")
        try:
            bot.reply_to(message, "An error occurred while saving. Please try again.")
        except Exception as e2:
            print(f"Error sending error message in process_link_step: {e2}")


@bot.message_handler(commands=['list'])
def list_keywords_command(message):
    print(f"DEBUG: Received /list command from chat ID: {message.chat.id}")
    print(f"DEBUG: Current keywords for /list: {list(keywords.keys())}") # Print only keys
    if not keywords:
        print("DEBUG: No keywords found, sending 'No keywords' message.")
        try:
            bot.reply_to(message, "No keywords are currently stored.")
        except Exception as e:
             print(f"Error sending 'No keywords' message: {e}")
        return
    response = "📄 Stored keywords:\n\n"
    for kw in keywords.keys():
        response += f"🔑 `{kw}`\n" # Using markdown again
    if len(response) > 4096:
        response = response[:4090] + "\n(...list truncated)"
    try:
        print(f"DEBUG: Attempting to send list response (Markdown)")
        bot.reply_to(message, response, parse_mode="Markdown")
        print(f"DEBUG: Successfully sent list response (Markdown).")
    except Exception as e:
        print(f"Error sending list (Markdown): {e}")
        # Fallback to plain text
        try:
            response_plain = "Stored keywords:\n\n" + "\n".join(keywords.keys())
            if len(response_plain) > 4096:
                 response_plain = response_plain[:4090] + "\n(...list truncated)"
            print(f"DEBUG: Attempting to send list response (Plain Text Fallback)")
            bot.reply_to(message, response_plain)
            print(f"DEBUG: Successfully sent list response (Plain Text Fallback).")
        except Exception as e2:
            print(f"Error sending list (Plain Text Fallback): {e2}")
            try:
                 bot.reply_to(message, "Error displaying list.")
            except Exception as e3:
                 print(f"Error sending final error message for /list: {e3}")

@bot.message_handler(commands=['remove'])
def remove_keyword_prompt(message):
    print(f"DEBUG: Received /remove command from chat ID: {message.chat.id}")
    if not keywords:
        try:
            bot.reply_to(message, "There are no keywords to remove.")
        except Exception as e:
            print(f"Error sending 'no keywords to remove' message: {e}")
        return
    try:
        msg = bot.send_message(message.chat.id, "🗑️ Which keyword do you want to remove? (Type the exact keyword)")
        bot.register_next_step_handler(msg, process_remove_keyword_step)
    except Exception as e:
        print(f"Error in remove_keyword_prompt: {e}")
        try:
            bot.reply_to(message, "An error occurred trying to start the removal process.")
        except Exception as e2:
             print(f"Error sending error message in remove_keyword_prompt: {e2}")

def process_remove_keyword_step(message):
    print(f"DEBUG: process_remove_keyword_step, attempting to remove: '{message.text}'")
    try:
        keyword_to_remove = message.text.strip()
        if keyword_to_remove in keywords:
            del keywords[keyword_to_remove]
            save_keywords(keywords)
            bot.send_message(message.chat.id, f"✅ Keyword '{keyword_to_remove}' has been successfully removed.")
        else:
            bot.send_message(message.chat.id, f"⚠️ Keyword '{keyword_to_remove}' not found.")
    except Exception as e:
        print(f"Error in process_remove_keyword_step: {e}")
        try:
            bot.reply_to(message, "An error occurred during removal. Please try again.")
        except Exception as e2:
            print(f"Error sending error message in process_remove_keyword_step: {e2}")

@bot.message_handler(commands=['settings'])
def settings_command(message):
    print(f"DEBUG: Received /settings command from chat ID: {message.chat.id}")
    try:
        bot.reply_to(message, "⚙️ Admin settings are not yet implemented. Stay tuned for future updates!")
    except Exception as e:
         print(f"Error sending /settings reply: {e}")


# This handler should be last, and only process messages that are not commands.
@bot.message_handler(func=lambda message: message.text is not None and not message.text.startswith('/'), content_types=['text'])
def auto_reply_handler(message):
    # Added message.text is not None check for safety
    print(f"DEBUG: auto_reply_handler received non-command text: '{message.text}' from chat ID: {message.chat.id}")
    if message.text in keywords:
        reply_content = keywords[message.text]
        print(f"DEBUG: Found keyword '{message.text}' for auto-reply, replying with: '{reply_content[:50]}...'") # Log truncated reply
        disable_preview = not ("http://" in reply_content or "https://" in reply_content)
        try:
            bot.reply_to(message, reply_content, disable_web_page_preview=disable_preview)
        except Exception as e:
            print(f"Error sending auto-reply for keyword '{message.text}': {e}")
    # else:
        # print(f"DEBUG: Keyword '{message.text}' not found for auto-reply in {list(keywords.keys())}")

# --- Main Bot Loop ---
if __name__ == '__main__':
    # Check for API token before starting
    if API_TOKEN is None or API_TOKEN == "YOUR_FALLBACK_TOKEN_IF_ANY":
        print("CRITICAL: Bot cannot start without a valid TELEGRAM_API_TOKEN.")
    else:
        print("Setting bot commands...")
        set_bot_commands()
        print("Bot is starting...")
        try:
            bot.polling(none_stop=True, interval=0) # interval=0 might help with responsiveness
        except Exception as e:
            print(f"Bot polling error: {e}")
        finally:
            print("Bot has stopped.")