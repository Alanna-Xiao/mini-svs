FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MINI_SVS_VOICEBANK_DIR=/app/assets/voicebanks \
    MINI_SVS_INSTRUMENT_CONFIG=/app/assets/instruments/instruments.json \
    MINI_SVS_OUTPUT_DIR=/app/data/outputs

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fluidsynth \
        libsndfile1 \
        rubberband-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
RUN python -m pip install --no-cache-dir /app/backend

COPY voicebanks/author_demo/voicebank.json /app/assets/voicebanks/author_demo/voicebank.json
COPY voicebanks/author_demo/samples /app/assets/voicebanks/author_demo/samples
COPY instruments/instruments.container.json /app/assets/instruments/instruments.json
COPY instruments/musescore_general/MuseScore_General.sf3 /app/assets/instruments/musescore_general/MuseScore_General.sf3

RUN useradd --create-home --uid 10001 mini-svs \
    && mkdir -p /app/data/outputs \
    && chown -R mini-svs:mini-svs /app/data

USER mini-svs
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
