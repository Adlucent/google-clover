FROM python:3.7-buster

ENV PYTHONPATH=/usr/app/site:/usr/app/site/vendor \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /usr/app

COPY ./site/requirements/base.txt ./requirements/base.txt
COPY ./site/requirements/local.txt ./requirements/local.txt
COPY ./site/requirements.txt ./

RUN pip install -r ./requirements/local.txt

RUN apt-get update && \
    apt-get install -y -q fonts-nanum

CMD /bin/bash
