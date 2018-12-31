FROM python:3

ADD bot.py /
ADD requirements.txt /

RUN mkdir /config
RUN mkdir /code
RUN mkdir /vol

ADD ./requirements.txt /config/

RUN pip install -r /config/requirements.txt

ADD . /code/
ADD ./requirements.txt /config/
ADD . /code/vol/

WORKDIR /code

RUN pip install -r /config/requirements.txt

CMD [ "python", "bot.py" ]