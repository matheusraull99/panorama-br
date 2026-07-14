# Imagem base dos extratores Bronze (Cloud Run Jobs)
FROM python:3.13-slim

# Usuário não-root
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY jobs/ ./jobs/

USER appuser

# O job a rodar é definido por env var (ex: jobs.bronze.bacen_sgs) no Cloud Run Job
ENTRYPOINT ["python", "-m"]
CMD ["jobs.bronze.bacen_sgs"]
