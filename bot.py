import time
from datetime import datetime
from threading import Thread

import schedule
import telebot
from models import User, ToDo

API_TOKEN = str(open(file='api_token.txt', mode='r').read())
bot = telebot.TeleBot(API_TOKEN)


# /start
@bot.message_handler(commands=['start'], regexp=None, func=None, content_types=None, chat_types=None)
def start_handler(message):
    if not User.select().where(User.chat_id == message.chat.id):
        User.create(
            chat_id=message.chat.id,
            username=message.chat.username
        )
    bot.send_message(
        chat_id=message.chat.id,
        text=f'Hi, {message.chat.first_name} {message.chat.last_name or ""}'
    )


def create_all_todo_message(chat_id):
    user = User.get(User.chat_id == chat_id)
    todos = ToDo.select().where(
        ToDo.user == user,
        ToDo.date == datetime.now()
    )
    answer_message = []
    for index, todo in enumerate(todos):
        if todo.is_done:
            answer_message.append(f"<b>{index + 1}.</b> <s>{todo.task}</s>\n")
        else:
            answer_message.append(f"<b>{index + 1}.</b> <u>{todo.task}</u>\n")
    return "".join(answer_message)


# /today /t
@bot.message_handler(commands=['today', 't'])
def get_todo_list(message):
    bot.send_message(
        chat_id=message.chat.id,
        text=create_all_todo_message(message.chat.id),
        parse_mode='HTML'
    )


# "{int} done"
@bot.message_handler(regexp="\d+ done")
def make_done(message):
    todo_id = message.text.split(' ')[0]
    todo = ToDo.get(ToDo.id == todo_id)
    todo.is_done = True
    todo.save()

    bot.send_message(
        chat_id=message.chat.id,
        text=f"'{todo.task}' is Done now"
    )


# Any text message
@bot.message_handler(content_types=['text'])
def create_todo_handler(message):
    user = User.get(User.chat_id == message.chat.id)
    ToDo.create(
        task=message.text,
        is_done=False,
        user=user,
        date=datetime.now()
    )
    bot.send_message(
        chat_id=message.chat.id,
        text="Your ToDo was saved"
    )


def check_notify():
    for user in User.select():
        if ToDo.select().where(
                ToDo.user == user,
                ToDo.date == datetime.now(),
                ToDo.is_done == False
        ):
            bot.send_message(
                chat_id=user.chat_id,
                text=create_all_todo_message(user.chat_id),
                parse_mode="HTML"
            )


# INSTEAD OF: create 1 more file for this thread:
def run_scheduler():
    schedule.every(5).seconds.do(check_notify)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    Thread(target=run_scheduler).start()
    bot.infinity_polling()
