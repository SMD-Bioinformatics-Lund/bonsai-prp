# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /usr/src/app

# Clone the repository and install dependencies
RUN git clone --depth 1 https://github.com/Clinical-Genomics-Lund/bonsai-prp.git && \
    cd bonsai-prp && \
    pip install -e . && \
    pip install biopython

# Set umask
RUN umask 0002

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp" \
      version="0.3.1"

# Default command to run when the container starts
CMD ["python"]
