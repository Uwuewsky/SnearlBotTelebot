from telebot import types
from data.config import earl, vity, apog, mity, delv, dela

#Клавиатура для работы с БД
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    btn1 = types.KeyboardButton('/' + earl)
    btn2 = types.KeyboardButton('/' + vity)
    btn3 = types.KeyboardButton('/' + apog)
    btn4 = types.KeyboardButton('/' + delv)
    btn5 = types.KeyboardButton('/' + dela)
    btn6 = types.KeyboardButton('/voicelist')
    btn7 = types.KeyboardButton('/' + mity)
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return keyboard