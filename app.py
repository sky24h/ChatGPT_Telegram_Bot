import datetime
import traceback
import asyncio
import signal
import os
import json

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, AIORateLimiter

from openai_utils import ChatGPT


def handle_timeout(signum, frame):
    raise TimeoutError("Request Timeout")

# set APIs
# get api_key from config.json
with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
    config = json.load(f)
telegram_bot_api = config['telegram_bot_token']

chatgpt = ChatGPT(config['openai_api_key'])

# default prompt
chat_prompt = "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible using the same language to the user"

welcome_message = "Welcome to ChatGPT, an AI chatbot powered by GPT-3.5-turbo. I'm here to assist you with various language-related tasks. \nAs a language model, I can help you with:\n- Generating text\n- Answering questions\n- Translating text\n- Summarizing long blocks of text\n- Completing forms\n- Generating recommendations\n- Natural language processing\n- Sentiment analysis\n- Providing general knowledge or trivia\n- Scheduling appointments\n\nPlease keep in mind that these are not the only things I can do. If you have a specific request, feel free to ask me! Let's get started."
welcome_message += "\n\nI'm able to remember what we've talked within 24 hours. If you want to clear the chat history manually, you can send 'clear' to me."

# python prompt
python_prompt = 'You are a concise Python assistant that responds to future inquiries within ["""] blocks.'
python_welcome = 'Welcome to Python Mode! You can ask me to write Python code according to your needs!'

# cpp prompt
cpp_prompt = 'You are a concise C++ assistant that responds to future inquiries within ["""] blocks.'
cpp_welcome = 'Welcome to C++ Mode! You can ask me to write C++ code according to your needs!'

# japanese prompt
japanese_prompt = 'You are a Japanese assistant that can translate and write articles in Japanese. Regardless of what the user says, you will always respond in Japanese.'
japanese_welcome = 'Welcome to Japanese Translation and Writing Mode! You can ask me to translate Chinese into Japanese or write a Japanese article according to your needs!'

# academic prompt
academic_prompt = 'You are an academic assistant that can proofread and write academic papers, with formal language and correct grammar.'
academic_welcome = 'Welcome to Academic Writing Mode! You can ask me to write an academic paper according to your needs!'

# use gpt-4 prompt
gpt4_welcome = 'Welcome to GPT-4 Mode!'

import logging
# save log to file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler('chatgpt.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# default mode
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User: " + str(update.effective_user.id) + " Reset to Default Chat Mode")
    user_id = update.effective_user.id
    chatgpt.reset_chat(user_id, chat_prompt)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

# python mode
async def python(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User: " + str(update.effective_user.id) + " Reset to Python Mode")
    user_id = update.effective_user.id
    chatgpt.reset_chat(user_id, python_prompt)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=python_welcome)

# cpp mode
async def cpp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User: " + str(update.effective_user.id) + " Reset to C++ Mode")
    user_id = update.effective_user.id
    chatgpt.reset_chat(user_id, cpp_prompt)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=cpp_welcome)

# japanese mode
async def japanese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User: " + str(update.effective_user.id) + " Reset to Chinese-Japanese Translation and Writing Mode")
    user_id = update.effective_user.id
    chatgpt.reset_chat(user_id, japanese_prompt)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=japanese_welcome)

# academic mode
async def academic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User: " + str(update.effective_user.id) + " Reset to Academic Writing Mode")
    user_id = update.effective_user.id
    chatgpt.reset_chat(user_id, academic_prompt)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=academic_welcome)

async def gpt4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_api = chatgpt.switch_api(user_id)
    logger.info("User: " + str(update.effective_user.id) + " Switch API to {}".format(current_api))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=gpt4_welcome.replace('GPT-4', current_api))

def reduce_messeges(user_id, e):
    logger.info("User: " + str(user_id) + " Current messages are too long, now trying to reduce length.")
    if len(messages[user_id]) > 3:
        messages[user_id] = messages[user_id][:1] + messages[user_id][3:]
        logger.info("User: " + str(user_id) + " Forget first two messages to reduce length")
        return False
    else:
        logger.error("User: " + str(user_id) + " Error while sovling: " + str(e) + " Messages are too long, please try to reduce your message length")
        raise Exception(error)

# answer function
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get user id and message
    user_id = update.effective_user.id
    user_message = update.message.text
    try:
        # get chatgpt answer and update messages and tokens, except getting clear or exit
        if user_message == "clear" or user_message == "exit":
            chatgpt.reset_chat(user_id, chat_prompt)
            logger.info("User: " + str(user_id) + " Clear chat history")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Chat history cleared, now let's start over!")
        else:
            placeholder_message = await update.message.reply_text("...")
            # send typing action
            await update.message.chat.send_action(action="typing")
            signal.signal(signal.SIGALRM, handle_timeout)
            signal.alarm(60)
            Success = False
            count = 0
            while not Success:
                count += 1
                if count > 5:
                    logger.error("User: " + str(user_id) + " Error: Too many times of retry")
                    raise Exception("Too many times of retry")
                try:
                    for status, answer in chatgpt.chat(user_id, user_message):
                        if status == "streaming":
                            answer = answer+'...'
                        elif status == "finished":
                            Success = True
                            logger.info("User: " + str(user_id) + " Message: " + user_message + " Answer: " + answer)
                        else:
                            raise Exception("Unknown status: " + status)
                        await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=ParseMode.HTML)

                except Exception as e:
                    if "maximum" in str(e):
                        Success = reduce_messeges(user_id, e)
                    else:
                        logger.error("User: " + str(user_id) + " Message: " + user_message + " Error: " + str(e))
                        raise e
                finally:
                    signal.alarm(0)


    except Exception as e:
        # if error, return error message
        answer = "Oops, something went wrong. Please try again later or contact @sky24h for help."
        answer += "\n\nError Message: " + str(e)
        logger.error("User: " + str(user_id) + " Message: " + user_message + " Error: " + str(e))
        traceback.print_exc()
        await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=ParseMode.HTML)


if __name__ == '__main__':
    # get telegram bot api
    application = ApplicationBuilder().token(telegram_bot_api).build()
    
    # add handlers
    start_handler = CommandHandler('start', start)
    python_handler = CommandHandler('python', python)
    cpp_handler = CommandHandler('cpp', cpp)
    japanese_handler = CommandHandler('japanese', japanese)
    academic_handler = CommandHandler('academic', academic)
    gpt4_handler = CommandHandler('gpt4', gpt4)

    # answer to all text messages except commands
    answer_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), answer)

    # add handlers to application
    application.add_handler(start_handler)
    application.add_handler(python_handler)
    application.add_handler(cpp_handler)
    application.add_handler(japanese_handler)
    application.add_handler(academic_handler)
    application.add_handler(gpt4_handler)
    application.add_handler(answer_handler)

    # start polling
    logger.info("Start polling at time: " + str(datetime.datetime.now()))
    application.run_polling()
