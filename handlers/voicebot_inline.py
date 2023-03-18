from data.bot_instance import bot
from telebot import types
from services.databases import voicelist

end_num = 0 #Глобальная переменная, хранящая в себе айдишник войса, с которого стоит начинать
#подгрузку при достижении максимального кол-ва рез-тов в выдаче (50 штук)

#Инлайн-запросы для вывода списка определенных войсов
@bot.inline_handler(lambda query: query.query.lower() == 'эрл'
                    or query.query.lower() == 'вытя'
                    or query.query.lower() == 'апоганда'
                    or query.query.lower() == 'митя')
def query_message(inline_query):

    counter = len(voicelist)
    idlist = []
    kolvo = 0
    output_list = []

    if inline_query.query.lower() == 'эрл':
        voice_type = 'Earl'
    elif inline_query.query.lower() == 'вытя':
        voice_type = 'Vytiran'
    elif inline_query.query.lower() == 'апоганда':
        voice_type = 'Apoganda'
    elif inline_query.query.lower() == 'митя':
        voice_type = 'Mitya'


    offset = int(inline_query.offset) if inline_query.offset else 1
    #Добавление результатов в выдачу инлайн-бота, их отправка и подгрузка при достижении максимума (50 штук)
    try:
        global end_num
        for i in range(end_num, counter):
            if voicelist[i][0] == voice_type:
                kolvo+=1
                idlist.append(i)
            if kolvo == 50:
                end_num = i+1
                break
        for i in idlist:
            output_list.append(types.InlineQueryResultVoice(i, voicelist[i][2], voicelist[i][1]))

        if len(output_list) < 50:
            bot.answer_inline_query(inline_query.id, output_list, cache_time=1, is_personal = True)
            end_num = 0
        else:
            bot.answer_inline_query(inline_query.id, output_list, cache_time=1, is_personal = True, next_offset = str(offset + 50))

    except Exception:
        return

#Поиск по всем войсам в БД
@bot.inline_handler(lambda query: len(query.query) > 1)
def query_search(inline_query):

    counter = len(voicelist)
    output_list = []

    try:
        for i in range(counter):
            if inline_query.query.lower() in voicelist[i][1].lower():
                output_list.append(types.InlineQueryResultVoice(i, voicelist[i][2], voicelist[i][1]))
        bot.answer_inline_query(inline_query.id, output_list, cache_time=1, is_personal = True)
    except Exception:
        return