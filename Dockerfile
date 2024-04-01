FROM python:3.11
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y upgrade
RUN apt-get install --fix-missing -y nginx net-tools gettext libxml2-dev libxslt-dev openssl python3-lxml wkhtmltopdf

RUN mkdir /code
WORKDIR /code
RUN mkdir media static logs
#ENV PYTHONWARNINGS="always"

RUN apt-get install -y locales
RUN echo "Europe/Helsinki" > /etc/timezone && \ 
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# fi_FI.UTF-8 UTF-8/fi_FI.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="fi_FI.UTF-8"'>/etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=fi_FI.UTF-8
RUN locale -a
RUN export LOCALE_PATHS="/usr/share/i18n"

COPY ./django_local_nginx.conf /etc/nginx/sites-available/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code

EXPOSE 8000
COPY ./run.sh /
ENTRYPOINT ["/run.sh"]
