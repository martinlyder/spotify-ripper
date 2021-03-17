FROM ubuntu:focal

# Für spotify-ripper benötigte Pakete installieren
RUN apt update && \
    apt install git lame build-essential libffi-dev python3-setuptools python3-pip wget -y && \
    apt remove python3-requests -y

# libspotify installieren (add mopidy's libspotify repository & install libspotify from mopidy's repository)
RUN wget -q -O - https://apt.mopidy.com/mopidy.gpg | apt-key add - && \
    wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list && \
    apt update && apt install libspotify12 libspotify-dev python-spotify -y --no-install-recommends

# Set encoding and language
RUN apt install -y locales && locale-gen de_DE.UTF-8
ENV LANG='de_DE.UTF-8' LANGUAGE='de_DE.UTF-8' LC_ALL='de_DE.UTF-8'
ENV PYTHONIOENCODING utf-8

# User erstellen und Anwendung bauen
RUN useradd -rm -d /home/ripper -s /bin/bash -g users -G sudo -u 1000 ripper
COPY * /home/ripper/source-code/
COPY spotify_ripper /home/ripper/source-code/spotify_ripper
WORKDIR /home/ripper/source-code
RUN python3 setup.py install

RUN echo 'ripper:Auu3rf3s2m' | chpasswd
RUN chown ripper -R /home/ripper/ && chgrp users -R /home/ripper/
WORKDIR /home/ripper/
USER ripper
RUN mkdir -p /home/ripper/data
CMD spotify-ripper -u $SPOTIFY_USER -p $SPOTIFY_PASSWORD /home/ripper/data/uris_to_download.txt
