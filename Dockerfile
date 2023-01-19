FROM python:3-slim

WORKDIR /uffbot

ADD requirements.txt .
ADD /uffbot ./uffbot
ADD main.py .

# install uffbots requirements
RUN pip install -r requirements.txt

# install ffmpeg
RUN apt-get update
RUN apt-get install -y ffmpeg

ENTRYPOINT ["python3", "main.py"]
