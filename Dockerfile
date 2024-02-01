# Stage 1: Builder image
FROM python:3.11 AS builder

# Set the working directory in the builder image
WORKDIR /usr/src/app

# Pip install bonsai-prp & dependencies
RUN pip install --upgrade pip && \
    pip install bonsai-prp biopython

# Install build dependencies
RUN apt-get update && \
    apt-get install -y gcc make wget xz-utils apt-utils git && \
    rm -rf /var/lib/apt/lists/*

# Download and install sambamba
RUN wget https://github.com/biod/sambamba/releases/download/v1.0.1/sambamba-1.0.1-linux-amd64-static.gz && \
    gunzip sambamba-1.0.1-linux-amd64-static.gz && \
    chmod +x sambamba-1.0.1-linux-amd64-static && \
    mv sambamba-1.0.1-linux-amd64-static /usr/bin/sambamba

# Download Picard
RUN wget -O /usr/bin/picard.jar https://github.com/broadinstitute/picard/releases/download/3.1.1/picard.jar

# Download and compile samtools
RUN wget https://github.com/samtools/samtools/releases/download/1.19.2/samtools-1.19.2.tar.bz2 && \
    tar -xvf samtools-1.19.2.tar.bz2 && \
    rm samtools-1.19.2.tar.bz2 && \
    cd samtools-1.19.2 && \
    make install

# Stage 2: Final image
FROM python:3.11

# Copy only the necessary files from the builder image
COPY --from=builder /usr/src/app /usr/src/app
COPY --from=builder /usr/bin/sambamba /usr/bin/sambamba
COPY --from=builder /usr/bin/picard.jar /usr/bin/picard.jar
COPY --from=builder /usr/local/bin/samtools /usr/local/bin/samtools

# Set the working directory in the final image
WORKDIR /usr/src/app

# Set umask
RUN umask 0002

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp" \
      version="0.3.1"

# Default command to run when the container starts
CMD ["python"]
