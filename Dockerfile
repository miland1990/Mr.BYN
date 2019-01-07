FROM python:3

RUN mkdir code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

CMD [ "python", "bot.py" ]