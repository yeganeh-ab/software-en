import logging
import pandas as pd
import requests
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    InlineQueryHandler,
    CallbackQueryHandler
)
from uuid import uuid4
from datetime import datetime

def read_csv_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return pd.DataFrame() 

TOKEN = "7894600697:AAFHdFqFzG-JrE3FZB8G8xUlVO9zehLWP3c"

HELP_COMMAND_RESPONSE = """
Greetings! Here are the commands you can use with this bot:

/start -> Begin interacting with the bot
/time -> Receive the current time from the bot
/fact -> get some interesting facts
/help -> Display this message again
And by using @University_Projectbot you can see the information of your favorite application
Feel free to utilize any of these commands as needed. If you require further assistance, don't hesitate to ask. Farewell for now!
"""

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Dear {update.effective_user.username}, welcome to our robot!"
    )

async def time_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=current_time,
        reply_to_message_id=update.effective_message.id
    )

async def fact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
    fact = data.json()["text"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=fact)

async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_COMMAND_RESPONSE,
        reply_to_message_id=update.effective_message.id
    )

def get_reviews_for_app(reviews_data, app_name, num_reviews=5):
    filtered_reviews = reviews_data[reviews_data['App'] == app_name]
    return filtered_reviews.head(num_reviews)  

def format_reviews(reviews):
    if reviews.empty:
        return "No reviews found for this application."
    
    review_messages = []
    for index, row in reviews.iterrows():
        review_messages.append(f"Review {index + 1}:\n{row['Translated_Review']}\nSentiment: {row['Sentiment']}\n")
    
    return "\n".join(review_messages)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # دریافت نام اپلیکیشن از callback_data
    app_name = query.data.split(":")[1]

    # دریافت 5 نظر مرتبط با اپلیکیشن
    reviews_file_path = r"E:\project\app bot\googleplaystore_user_reviews.csv"
    reviews_data = read_csv_data(reviews_file_path)
    reviews = get_reviews_for_app(reviews_data, app_name)[:5]  # فقط 5 نظر اول
    formatted_reviews = format_reviews(reviews)

    await context.bot.send_message(chat_id=query.from_user.id, text=formatted_reviews)
  

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    logger.info(f"Received inline query: {query}")  
    if not query:
        await context.bot.answer_inline_query(update.inline_query.id, [])
        return
    
    file_path = r"E:\project\app bot\googleplaystore.csv"  
    data = read_csv_data(file_path)
    
    if data.empty:
        logger.error("No data found in the CSV file.")
        await context.bot.answer_inline_query(update.inline_query.id, [])
        return

    results = []
    filtered_data = data[data['App'].str.contains(query, case=False, na=False)]
    
    logger.info(f"Filtered data: {filtered_data}")  # Log the filtered data

    if filtered_data.empty:
        logger.info("No matching apps found.")
        await context.bot.answer_inline_query(update.inline_query.id, [])
        return

    for index, row in filtered_data.iterrows():
        keyboard = [
            [InlineKeyboardButton("Show 5Reviews", callback_data=f"show_reviews:{row['App']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=row['App'],
                input_message_content=InputTextMessageContent(
                    message_text=f"Title: {row['App']}\n"
                                 f"Rating: {row['Rating']}\n"
                                 f"Category: {row['Category']}\n"
                                 f"Number of Reviews: {row['Reviews']}\n"
                                 f"Size: {row['Size']}\n"
                                 f"Installs: {row['Installs']}\n"
                                 f"Type: {row['Type']}\n"
                                 f"Price: {row['Price']}\n"
                                 f"Content Rating: {row['Content Rating']}\n"
                                 f"Genres: {row['Genres']}\n"
                                 f"Last Updated: {row['Last Updated']}\n"
                                 f"Current Version: {row['Current Ver']}\n"
                                 f"Android Version: {row['Android Ver']}\n"
                                
                ),
                description=f"Rating: {row['Rating']}, Category: {row['Category']}, Number of Reviews: {row['Reviews']}",
                reply_markup=reply_markup 
            )
        )
    await context.bot.answer_inline_query(update.inline_query.id, results)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error} on Update {update}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler("help", help_command_handler))
    application.add_handler(CommandHandler("time", time_command_handler))
    application.add_handler(CommandHandler("fact", fact_handler))
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CallbackQueryHandler(button_handler)) 
    application.add_error_handler(error_handler)

    application.run_polling()
