# Version 1.0 template-transformer-simple 
FROM opendronemap/odm:2.1.0
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

RUN useradd -u 49044 extractor \
    && mkdir /home/extractor \
    && chown -R extractor /home/extractor \
    && chgrp -R extractor /home/extractor

COPY requirements.txt packages.txt /home/extractor/

USER root

# Install Python3.7
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
    python3.7 \
    python3-pip \
    && rm /usr/bin/python3 /usr/bin/python3m \
    && ln -s /usr/bin/python3.7 /usr/bin/python3 \
    && ln -s /usr/bin/python3.7m /usr/bin/python3m \
    && ln -s /usr/bin/python3.7 /usr/bin/python \
    && python3.7 -m pip install -U pip \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN [ -s /home/extractor/packages.txt ] && \
    (echo 'Installing packages' && \
        apt-get install -y gdal-bin libgdal-dev gcc g++ && \
        cat /home/extractor/packages.txt | xargs apt-get install -y --no-install-recommends && \
        apt-get install -y python3.7-dev python3-wheel && \
        rm /home/extractor/packages.txt && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*) || \
    (echo 'No packages to install' && \
        rm /home/extractor/packages.txt)

RUN (echo "installing osgeo dependencies" && \
    apt-get update && \
    apt-get install -y python3-gdal gdal-bin libgdal-dev gcc g++ python3.7-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*)

RUN [ -s /home/extractor/requirements.txt ] && \
    (echo 'Install python modules' && \
    python3.7 -m pip install --upgrade --no-cache-dir pip && \
    python3.7 -m pip install --upgrade --no-cache-dir setuptools && \
    python3.7 -m pip install --upgrade --no-cache-dir numpy && \
    python3.7 -m pip install --no-cache-dir -r /home/extractor/requirements.txt && \
    rm /home/extractor/requirements.txt) || \
    (echo 'No python modules to install' && \
     rm /home/extractor/requirements.txt)

RUN rm /usr/bin/python /usr/bin/python3 /usr/bin/python3m && \
    ln -s /usr/bin/python3.6 /usr/bin/python && \
    ln -s /usr/bin/python3.6 /usr/bin/python3 && \
    ln -s /usr/bin/python3.6m /usr/bin/python3m && \
    python3.7 -m pip install setuptools

USER extractor
COPY configuration.py odm.py worker.py settings.yaml /home/extractor/

USER root
RUN chmod a+x /home/extractor/odm.py

USER extractor
ENTRYPOINT ["/home/extractor/odm.py"]

ENV PYTHONPATH="${PYTHONPATH}:/code"
