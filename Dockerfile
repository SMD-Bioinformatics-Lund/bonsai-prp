# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Pip install bonsai-prp & dependencies
RUN pip install --upgrade pip &&\
    pip install bonsai-prp && \
    pip install biopython

RUN apt update &&\
    apt-get install -y gcc make wget xz-utils git &&\
    wget https://github.com/biod/sambamba/releases/download/v1.0.1/sambamba-1.0.1-linux-amd64-static.gz &&\
    gunzip sambamba-1.0.1-linux-amd64-static.gz &&\
    chmod +x sambamba-1.0.1-linux-amd64-static &&\
    mv sambamba-1.0.1-linux-amd64-static /usr/bin/sambamba &&\
    wget -O /usr/bin/picard.jar https://github.com/broadinstitute/picard/releases/download/3.1.1/picard.jar &&\
    wget https://github.com/samtools/samtools/releases/download/1.19.2/samtools-1.19.2.tar.bz2 &&\
    tar -xvf samtools-1.19.2.tar.bz2 &&\
    cd samtools-1.19.2 &&\
    make install

# Set umask
RUN umask 0002

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp" \
      version="0.3.1"

# Default command to run when the container starts
CMD ["python"]
