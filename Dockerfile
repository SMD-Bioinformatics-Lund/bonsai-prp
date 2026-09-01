# Stage 1: Docker build stage
FROM python:3.11 AS build-stage

# Set the working directory in the builder image
WORKDIR /usr/src/app

# Copy the contents of the local directory into the container
COPY . .

# Install wget
RUN apt-get update && \
    apt-get install -y gcc make wget xz-utils apt-utils && \
    rm -rf /var/lib/apt/lists/*

# Pip install bonsai-prp & dependencies
RUN pip install --upgrade pip && \
    pip install ".[all]"

# Stage 2: Final image
FROM python:3.11

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set the working directory in the final image
WORKDIR /usr/src/app

# Install tzdata
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary files from the builder image
COPY --from=build-stage /usr/local/bin/prp /usr/local/bin/prp
COPY --from=build-stage /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Set umask
RUN umask 0002

# Metadata as described above
LABEL authors="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      maintainers="Markus Johansson <markus.h.johansson@skane.se>, Ryan Kennedy <ryan.kennedy@skane.se>" \
      description="Docker image for bonsai-prp"

# Default command to run when the container starts
CMD ["python"]
