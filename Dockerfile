FROM martinkist/discord.py-docker:latest

WORKDIR /uffbot

ADD requirements.txt .
ADD /uffbot ./uffbot
ADD main.py .

# install uffbots requirements
RUN pip install -r requirements.txt

#ENTRYPOINT ["ls"]
ENTRYPOINT ["python3", "main.py"]
