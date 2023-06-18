FROM python:3.11
WORKDIR /SnearlBotTelebot
COPY . /SnearlBotTelebot/
RUN pip install -r requirements.txt
CMD ["python", "start_bot.py"]