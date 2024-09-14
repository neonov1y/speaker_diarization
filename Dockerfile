FROM python:3.10
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 libsndfile1-dev 
RUN pip install -r requirements.txt

CMD [ "python", "--version"]
