import telebot
import sqlite3
from telebot import types


bot = telebot.TeleBot('6110618451:AAE6A7xirMcQvkx-s8Uiwv2312pr8N7a0gM')
# Connect to database
db = sqlite3.connect('user_words.db', check_same_thread=False)
c = db.cursor()

user_id = None
user_name = None

#Global murlkup and buttons, which used in many functions:

murkup = types.InlineKeyboardMarkup()
add_btn = types.InlineKeyboardButton('Add new words pare', callback_data='add') #Add new words pare in db
delete_btn = types.InlineKeyboardButton('Delete words pare', callback_data='delete') #Delete selected words pare from db
edit_btn = types.InlineKeyboardButton('Edit existing words pare', callback_data='edit') #Edit existing words pare from db
test_btn = types.InlineKeyboardButton('Test your knowledge', callback_data='test') #
all_btn = types.InlineKeyboardButton('Show all words', callback_data='all') #

@bot.message_handler(commands=['start'])
def start(message):
    global user_id, user_name
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    print(user_id)

    murkup.row(add_btn, edit_btn)
    murkup.row(delete_btn, all_btn)
    murkup.row(test_btn)


    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}!', reply_markup=murkup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
     if callback.data == 'add':
        #Create a table with users to save their id and name
        c.execute("CREATE TABLE IF NOT EXISTS users (user_id NOT NULL UNIQUE, name varchar(50))")

        id = c.execute("SELECT user_id FROM users WHERE user_id = %s" % user_id)
        id = id.fetchone()[0]
        print(id)
        #Check if user hasn't been already get in database
        if user_id != id:
            c.execute("INSERT INTO users VALUES (?, ?)", (user_id, user_name))
        #Create a table for words pares
        c.execute("CREATE TABLE IF NOT EXISTS '%s' (EngWord varchar(50), TranslateWord varchar(50))" % user_id)
        #Insert user_id and user_name into user table
        db.commit()
        bot.send_message(callback.message.chat.id, 'Write eng words and translate(eng word - translate)')

@bot.message_handler(content_types = ['text'])
def save_words(message):
    eng_word, translate_word = message.text.split('-')
    eng_word = eng_word.strip()
    translate_word = translate_word.strip()

    words = (
        # {'id': user_id, 'eng': eng_word, 'trans': translate_word},
          eng_word, translate_word
    )
    c.execute("INSERT INTO '%s' VALUES (?, ?)" % user_id, words)
    db.commit()
    bot.send_message(message.chat.id, f"It's your words {message.text}")

bot.polling(none_stop=True)
c.close()
db.close()
