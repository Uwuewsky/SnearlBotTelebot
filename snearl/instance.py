from telebot import TeleBot
from snearl.datalist import Datalist

_token = Datalist("token.json")
bot = TeleBot(_token.data)
del _token

_help_msg = """
SnearlBot умеет:
1. Удалять репосты из заблокированных чатов.
   a. Блокируем чат через /block;
   b. Теперь бот будет удалять репосты;
   c. Разблокировать чат можно через /allow;
   d. Посмотреть список можно через /blacklist;

2. Хранить и отправлять инлайн списки голосовых сообщений.
   a. Отвечаем на войс, например:
        /voice_add [ИмяАвтора] [КраткоеОписание];
   b. Вводим тег бота и имя автора:
        @SnearlBot [ИмяАвтора];
   c. Можно ввести поисковый запрос из текста описания;
   d. Удалить войс можно с помощью:
        /voice_delete [ИмяАвтора] [НомерВойса];
   e. Посмотреть список можно через /voicelist;
"""

@bot.message_handler(commands=["start", "help"])
def send_help(message):
    bot.send_message(message.chat.id, _help_msg)
    return
