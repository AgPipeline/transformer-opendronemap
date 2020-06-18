# Version 1.0 template-transformer-simple 
FROM opendronemap/odm:0.7.0
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

RUN useradd -u 49044 extractor \
    && mkdir /home/extractor \
    && chown -R extractor /home/extractor \
    && chgrp -R extractor /home/extractor

COPY requirements.txt packages.txt /home/extractor/

USER root

RUN [ -s /home/extractor/packages.txt ] && \
    (echo 'Installing packages' && \
        apt-get update && \
        cat /home/extractor/packages.txt | xargs apt-get install -y --no-install-recommends && \
        rm /home/extractor/packages.txt && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*) || \
    (echo 'No packages to install' && \
        rm /home/extractor/packages.txt)

RUN [ -s /home/extractor/requirements.txt ] && \
    (echo 'Install python modules' && \
    python3 -m pip install -U --no-cache-dir pip && \
    python3 -m pip install --no-cache-dir setuptools && \
    python3 -m pip install --no-cache-dir -r /home/extractor/requirements.txt && \
    rm /home/extractor/requirements.txt) || \
    (echo 'No python modules to install' && \
     rm /home/extractor/requirements.txt)

RUN (echo "installing sudo" && \
    apt-get update && \
    apt-get -y install sudo)

RUN (echo "installing osgeo dependencies" && \
    sudo apt-get install -y python3-gdal gdal-bin libgdal-dev gcc g++ python3.5-dev && \
    sudo python3 -m pip install --no-cache-dir pygdal==2.2.2.*)

USER extractor
ENTRYPOINT ["/home/extractor/entrypoint.py"]

COPY *.py settings.yaml /home/extractor/

ENV PYTHONPATH="${PYTHONPATH}:/code"
