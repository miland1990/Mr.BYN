FROM python:3

ADD bot.py /
ADD requirements.txt /

RUN mkdir /config
RUN mkdir /code

ADD ./requirements.txt /config/

RUN pip install -r /config/requirements.txt

ADD . /code/

WORKDIR /code

CMD [ "python", "bot.py" ]