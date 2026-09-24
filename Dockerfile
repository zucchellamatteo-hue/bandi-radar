# Fase 1: costruisce la plancia (React) con Node.
FROM node:22-alpine AS plancia
WORKDIR /plancia
COPY plancia/package.json plancia/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY plancia/ ./
RUN npm run build

# Fase 2: l'applicazione Python, con dentro i file della plancia gia' costruiti.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY fonti ./fonti
COPY --from=plancia /plancia/dist ./plancia/dist

# L'applicazione non gira come root. Stesso numero utente (10001) della raccolta: il volume degli
# allegati, creato dall'uno o dall'altro servizio, appartiene cosi' allo stesso utente.
RUN useradd --system --no-create-home --uid 10001 appuser \
    && mkdir -p /srv/allegati && chown appuser /srv/allegati
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
