from data.bot_instance import bot
from telebot import types
from data.config import kbrd, stop, earl, vity, apog, mity, delv, dela
from keyboards.regular_keyboards import main_keyboard
from services.databases import voicelist, write_to_voices

#Команда для вызова клавиатуры
@bot.message_handler(commands= [kbrd, stop])
def handle_insert(message):
    bot.send_message(message.chat.id, 'Приветствую на панели управления базой данных', reply_markup=main_keyboard())

#Команды для открытия режима загрузки файлов
@bot.message_handler(commands = [earl, vity, apog, mity])
def handle_insert(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('/' + stop)
    keyboard.add(btn1)
    if message.text == '/' + earl:
        voice_type = message.text[1:-11]
        bot.send_message(message.chat.id, 'Можно загрузить файлы для Эрла', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_voice, voice_type)
    if message.text == '/' + vity:
        voice_type = message.text[1:-11]
        bot.send_message(message.chat.id, 'Можно загрузить файлы для Вытирана', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_voice, voice_type)
    if message.text == '/' + apog:
        voice_type = message.text[1:-11]
        bot.send_message(message.chat.id, 'Можно загрузить файлы для Апоганды', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_voice, voice_type)
    if message.text == '/' + mity:
        voice_type = message.text[1:-11]
        bot.send_message(message.chat.id, 'Можно загрузить файлы для Мити', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_voice, voice_type)

#Добавление файла в БД
def get_voice(message, voice_type):
    if message.voice is not None:
        voice_id = message.voice.file_id
        caption = message.caption
        entry = [voice_type, caption, voice_id]

        voicelist.append(entry)
        write_to_voices()

        bot.send_message(message.chat.id, 'Войс \"' +str(caption)+ '\"' + ' для ' + voice_type + ' загружен')
        bot.register_next_step_handler(message, get_voice, voice_type)

    #Команда для остановки режима загрузки
    elif message.text == '/' + stop:
        bot.send_message(message.chat.id, 'Загрузка завершена', reply_markup=main_keyboard())

    #Сообщение при неправильном формате файла
    else:
        bot.send_message(message.chat.id, 'Не тот тип файла')
        bot.register_next_step_handler(message, get_voice, voice_type)

#Удаление файла из БД
@bot.message_handler(commands= [delv])
def handle_delete(message):
    try:
        delete_index = int(message.text[7:])-1
        voice_name = voicelist[delete_index][1]
        del voicelist[delete_index]
        bot.send_message(message.chat.id, 'Войс ' +voice_name+ ' удален.')
    except Exception:
        bot.send_message(message.chat.id, 'Неправильно указан (или не указан вовсе) номер.')
        return
    write_to_voices()

#Удаление всех файлов
@bot.message_handler(commands=[dela])
def handle_delete_quest(message):
    def handle_deleteall(message):
        if message.text == 'Да':
            voicelist.clear()
            write_to_voices()
            bot.send_message(message.chat.id, 'Все данные были удалены')
        else:
            bot.send_message(message.chat.id, 'Не было получено утвердительного ответа')
            return
    bot.send_message(message.chat.id, 'Точно удалить все данные?')
    bot.register_next_step_handler(message, handle_deleteall)