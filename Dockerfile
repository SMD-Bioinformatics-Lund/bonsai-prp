# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /usr/src/app

# Clone the repository and install dependencies
RUN pip install bonsai-prp \
    pip install biopython

# Set umask
RUN umask 0002

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp" \
      version="0.3.0"

# Default command to run when the container starts
CMD ["python"]
