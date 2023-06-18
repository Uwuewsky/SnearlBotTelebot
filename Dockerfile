FROM python:3.11
WORKDIR /SnearlBotTelebot
COPY . /SnearlBotTelebot/
EXPOSE 80/tcp
RUN pip install -r requirements.txt
CMD ["python", "start_bot.py"]