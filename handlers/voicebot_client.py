from data.bot_instance import bot
from keyboards.inline_keyboards import inline_keyboard
from services.databases import voicelist

#Отправка списка войсов с пагинацией в лс
@bot.callback_query_handler(func = lambda call: True)
def callback_handler(call):

    cur_call = (call.data).split()
    calltype = cur_call[0]
    page = int(cur_call[1])
    count = int(cur_call[2])
    v = []

    try:
        #Кнопка вперед
        if calltype== 'next':
            index = int(cur_call[3])
            page+=1

            for i in voicelist[25*(page-1):25*page]:
                v.append(str(index) + '. ' + str(i[0]) + '. ' + str(i[1]))
                index+=1
            markup = inline_keyboard(page, count, index)
            bot.edit_message_text('\n'.join(v), message_id = call.message.id, chat_id = call.message.chat.id, reply_markup=markup)
        #Кнопка назад
        elif calltype == 'back':
            index = int(cur_call[3])
            if page == count:
                index -= (index-1)%25 + 25
            else:
                index -= 50
            page -= 1
            #Вывод войсов на страницу
            for i in voicelist[25*(page-1):25*page]:
                v.append(str(index) + '. ' + str(i[0]) + '. ' + str(i[1]))
                index+=1
            markup = inline_keyboard(page, count, index)
            bot.edit_message_text('\n'.join(v), message_id = call.message.id, chat_id = call.message.chat.id, reply_markup=markup)
        #Номер страницы
        elif calltype == 'currentpage':
            bot.answer_callback_query(call.id, text=f'Страница {page} из {count}')
    except Exception:
        bot.edit_message_text('Скорее всего весь список был удален.', message_id = call.message.id, chat_id = call.message.chat.id)
        return

#Команда для получения списка войсов
@bot.message_handler(commands=['voicelist'])
def handle_output_all(message):
    page = 1
    count = int(len(voicelist)/25)+1

    index = 1
    v = []
    for i in voicelist[0:25]:
        v.append(str(index) + '. ' + str(i[0]) + '. ' + str(i[1]))
        index+=1
    markup=inline_keyboard(page, count, index)
    
    try:
        bot.send_message(message.from_user.id, '\n'.join(v), reply_markup=markup)
    except Exception:
        bot.send_message(message.chat.id, 'Напишите боту первым чтобы инициировать диалог.')
        return
