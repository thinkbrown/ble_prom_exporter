FROM python:alpine

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN apk add --no-cache build-base pkgconfig glib glib-dev
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del build-base pkgconfig glib-dev
COPY main.py ./
CMD [ "python", "./main.py", "/etc/ble_exporter.conf" ]
