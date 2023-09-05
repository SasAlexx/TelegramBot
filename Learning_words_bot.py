import telebot
import sqlite3
from telebot import types
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)


TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN)
# Connect to database
db = sqlite3.connect('user_words.db', check_same_thread=False)
c = db.cursor()

user_id = None
user_name = None
all_words = None
word_to_delete = None
#Global markup and buttons, which used in many functions:

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
add_btn = types.InlineKeyboardButton('Add new words pare', callback_data='add') #Add new words pare in db
edit_btn = types.InlineKeyboardButton('Edit', callback_data='edit') #Edit existing words pare from db
test_btn = types.InlineKeyboardButton('Test your knowledge', callback_data='test') #
all_btn = types.InlineKeyboardButton('Show all words', callback_data='all') #

@bot.message_handler(commands=['start'])
def start(message):
    global user_id, user_name, db, c

    db = sqlite3.connect('user_words.db', check_same_thread=False)
    c = db.cursor()

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    c.execute("CREATE TABLE IF NOT EXISTS users (user_id NOT NULL UNIQUE, name varchar(50))")

    id = list(c.execute("SELECT user_id FROM users WHERE user_id = %s" % user_id))
    if len(id) != 0:
        id = id[0][0]
    print(id)
    # Check if user hasn't been already get in database
    if user_id != id:
        c.execute("INSERT INTO users VALUES (?, ?)", (user_id, user_name))
    # Create a table for words pares
    c.execute("CREATE TABLE IF NOT EXISTS '%s' (WordID INT PRIMARY KEY, EngWord varchar(50) UNIQUE NOT NULL, TranslateWord varchar(50))" % user_id)
    # Insert user_id and user_name into user table
    db.commit()



    markup.row(add_btn, all_btn)
    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}!'
                                            f'\nChoose what you want to do by pressing th button',
                           reply_markup=markup)


@bot.message_handler(content_types=['text'])
def words_operations(message):
    global all_words
    if message.text == 'Add new words pare':
        msg = bot.send_message(message.chat.id, 'Write english word and accordance translate in format:'
                                                   '\nEhg word - Translate word')
        bot.register_next_step_handler(msg, add_word)
    elif message.text == 'Show all words':

        # print(all_words)
        words_markup = types.InlineKeyboardMarkup(row_width=2)
        show_list = ''
        number = 0
        word_index = 1
        all_words = c.execute("SELECT * FROM '%s'" % user_id)
        all_words = all_words.fetchall()
        print(*all_words, sep='\n')
        all_words = {eng_word : translate_word for eng_word, translate_word in all_words}
        print(all_words)
        for eng_word in all_words:
            words_markup.row(types.InlineKeyboardButton(f'{word_index}. {eng_word} - {all_words[eng_word]}',
                                                        callback_data=f'{eng_word}'))
            word_index += 1
        #Create a string to show all words from db to user
        for eng_word in all_words:
            number += 1
            show_list += f'{number}. {eng_word} - {all_words[eng_word]}\n'
        bot.send_message(message.chat.id, 'YOUR WORDS:', reply_markup=words_markup)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("delete_"))
def delete_word(callback):
    word_to_delete = callback.data.replace("delete_", "")
    delete_markup = types.InlineKeyboardMarkup()
    delete_markup.row(types.InlineKeyboardButton("Yes", callback_data=f'accept_{word_to_delete}'))
    bot.send_message(callback.message.chat.id, f'Are you sure you want to delete: {word_to_delete}', reply_markup=delete_markup)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("accept_"))
def accept_deleting(callback):
    word_to_delete = callback.data.replace("accept_", "")

    words = (
        # {'id': user_id, 'eng': eng_word, 'trans': translate_word},
        word_to_delete,
    )

    c.execute("DELETE FROM '%s' WHERE EngWord=?" % user_id, words)
    db.commit()

@bot.callback_query_handler(func=lambda callback: True)
def call_back(callback):

    if callback.data in all_words:
        # print(callback.data)
        word_markup = types.InlineKeyboardMarkup()
        delete_btn = types.InlineKeyboardButton('Delete', callback_data=f'delete_{callback.data}')  # Delete selected words pare from db

        word_markup.row(edit_btn, delete_btn)
        bot.send_message(callback.message.chat.id, f'{callback.data} - {all_words[callback.data]}', reply_markup=word_markup)

    elif callback.data == 'edit':
        msg = bot.send_message(callback.message.chat.id, 'Write english word and accordance translate in format:'
                                                   '\nEhg word - Translate word')
        bot.register_next_step_handler(msg, edit_word)

    elif callback.data == 'yes':
        c.execute('DELETE FROM %s WHERE CustomerName=' % user_id)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='Success!')



def add_word(message):
    if '-' in message.text:
        eng_word, translate_word = message.text.split('-')
        eng_word = eng_word.strip()
        translate_word = translate_word.strip()

        words = (
            # {'id': user_id, 'eng': eng_word, 'trans': translate_word},
              eng_word, translate_word
        )
        c.execute("INSERT INTO '%s' VALUES (?, ?)" % user_id, words)
        db.commit()

        bot.send_message(message.chat.id, f'Great! Its your words: {message.text}')
    else:
        bot.send_message(message.chat.id, 'Wrong format, try again.')


def edit_word(message):
    if '-' in message.text:
        eng_word, translate_word = message.text.split('-')
        eng_word = eng_word.strip()
        translate_word = translate_word.strip()

        words = (
            # {'id': user_id, 'eng': eng_word, 'trans': translate_word},
              eng_word, translate_word, eng_word
        )
        c.execute("UPDATE '%s' SET EngWord = ?, TranslateWord = ? WHERE EngWord = ?" % user_id, words)
        db.commit()
        bot.send_message(message.chat.id, f"Success! "
                                          f"\nYou've changed words to: {message.text}."
                                          f"\nCall 'Show all words' to see changes.")
    else:
        bot.send_message(message.chat.id, 'Wrong format, try again.')



bot.polling(none_stop=True)
c.close()
db.close()
