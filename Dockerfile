FROM python:3

ADD bot.py /
ADD requirements.txt /

RUN mkdir /config
RUN mkdir /code
RUN mkdir /vol

ADD ./requirements.txt /config/

RUN pip install -r /config/requirements.txt

ADD . /code/
ADD . /code/vol/

WORKDIR /code

VOLUME /$PWD/vol

CMD [ "python", "bot.py" ]