from telebot import types

#Инлайн-клавиатура к сообщению с выводом всех войсов
def inline_keyboard(page, count, index):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton('Назад', callback_data= f'back {page} {count} {index}')
    btn2 = types.InlineKeyboardButton(f'{page}/{count}', callback_data= f'currentpage {page} {count}')
    btn3 = types.InlineKeyboardButton('Вперед', callback_data= f'next {page} {count} {index}')
    if page == 1:
        keyboard.add(btn2, btn3)
    elif page > 1 and page < count:
        keyboard.add(btn1, btn2, btn3)
    elif page == count:
        keyboard.add(btn1, btn2)
    return keyboard