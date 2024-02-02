# Stage 1: Docker build stage
FROM python:3.11 AS build-stage

# Set the working directory in the builder image
WORKDIR /usr/src/app

# Copy the contents of the local directory into the container
#COPY . .

# Install wget
RUN apt-get update && \
    apt-get install -y gcc make wget xz-utils apt-utils && \
    rm -rf /var/lib/apt/lists/*

# Pip install bonsai-prp & dependencies
RUN pip install --upgrade pip && \
    #pip install . && \
    pip install bonsai-prp && \
    pip install biopython 

# Download and install Sambamba
RUN wget https://github.com/biod/sambamba/releases/download/v1.0.1/sambamba-1.0.1-linux-amd64-static.gz && \
    gunzip sambamba-1.0.1-linux-amd64-static.gz && \
    chmod +x sambamba-1.0.1-linux-amd64-static && \
    mv sambamba-1.0.1-linux-amd64-static /usr/bin/sambamba

# Download Picard
RUN wget https://github.com/broadinstitute/picard/releases/download/3.1.1/picard.jar && \
    chmod +x picard.jar && \
    mv picard.jar /usr/bin/picard.jar

# Download and compile samtools
RUN wget https://github.com/samtools/samtools/releases/download/1.19.2/samtools-1.19.2.tar.bz2 && \
    tar -xvf samtools-1.19.2.tar.bz2 && \
    rm samtools-1.19.2.tar.bz2 && \
    cd samtools-1.19.2 && \
    make install

# Stage 2: Final image
FROM python:3.11

# Set the working directory in the final image
WORKDIR /usr/src/app

# Install openjdk-17
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary files from the builder image
COPY --from=build-stage /usr/src/app /usr/src/app
COPY --from=build-stage /usr/bin/sambamba /usr/bin/sambamba
COPY --from=build-stage /usr/bin/picard.jar /usr/bin/picard.jar
COPY --from=build-stage /usr/local/bin/samtools /usr/local/bin/samtools
COPY --from=build-stage /usr/local/bin/prp /usr/local/bin/prp
COPY --from=build-stage /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Set umask
RUN umask 0002

# Set alias for Picard
RUN echo 'alias picard="java -jar /usr/bin/picard.jar"' >> ~/.bashrc

# Reload the shell to make the alias effective
RUN /bin/bash -c "source ~/.bashrc"

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp" \
      version="0.3.1"

# Default command to run when the container starts
CMD ["python"]
