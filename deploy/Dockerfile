# retro transformer -- Code Engine deployment image
FROM python:3.12-slim

WORKDIR /app

# stdlib-only: no pip install needed
COPY . /app

RUN chmod +x /app/pipeline/retro

# Run as a Code Engine job; pass the retro subcommand as job args, e.g.:
#   transform /data/HELLO.cbl --to java --mock
ENTRYPOINT ["python3", "/app/pipeline/retro"]
CMD ["--help"]
