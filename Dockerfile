FROM python:3.12-slim-bullseye

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/0.3.0/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.cargo/bin/:$PATH"

# Copy the project into the image
ADD . /app 
WORKDIR /app

# Sync the project into a new environment
RUN uv sync

# cert for cockroachdb
RUN curl --create-dirs -o $HOME/.postgresql/root.crt 'https://cockroachlabs.cloud/clusters/6b8e7f9d-0da6-419d-8312-a3f806965cc0/cert'

# Presuming there is a `my_app` command provided by the project
CMD ["uv", "run", "src/telegram_bot_tts/app.py"]