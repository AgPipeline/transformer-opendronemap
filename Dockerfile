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
        apt-get install software-properties-common && \
        add-apt-repository -y ppa:deadsnakes/ppa && \
        add-apt-repository -y ppa:ubuntugis/ppa && \
        apt-get update && \
        apt-get install -y gdal-bin libgdal-dev gcc g++ && \
        cat /home/extractor/packages.txt | xargs apt-get install -y --no-install-recommends && \
        apt-get install -y python3.7 && \
        ln -f /usr/bin/python3.7 /usr/bin/python3 && \
        ln -f /usr/bin/python3.7m /usr/bin/python3m && \
        python3 --version && \
        ogrinfo --version && \
        apt-get install -y python3.7-dev python3-wheel && \
        rm /home/extractor/packages.txt && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*) || \
    (echo 'No packages to install' && \
        rm /home/extractor/packages.txt)

RUN [ -s /home/extractor/requirements.txt ] && \
    (echo 'Install python modules' && \
    python3 -m pip install --upgrade --no-cache-dir pip && \
    python3 -m pip install --upgrade --no-cache-dir setuptools && \
    python3 -m pip install --upgrade --no-cache-dir numpy && \
    python3 -m pip install --no-cache-dir pygdal==2.2.2.* && \
    python3 -m pip install --no-cache-dir -r /home/extractor/requirements.txt && \
    rm /home/extractor/requirements.txt) || \
    (echo 'No python modules to install' && \
     rm /home/extractor/requirements.txt)

USER extractor
COPY configuration.py odm.py worker.py settings.yaml /home/extractor/

USER root
RUN chmod a+x /home/extractor/odm.py

USER extractor
ENTRYPOINT ["/home/extractor/odm.py"]

ENV PYTHONPATH="${PYTHONPATH}:/code"
