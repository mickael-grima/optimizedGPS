FROM python:2.7

MAINTAINER <mickael.grima@tum.de>

LABEL version="0.1"

RUN pip install tornado beautifulsoup4 ipython awscli requests
RUN apt-get install -y librsvg2-2

WORKDIR /workspace

RUN git clone https://github.com/mickael-grima/optimizedGPS.git
RUN python optimizedGPS/setup.py install

COPY . .

CMD python server.py