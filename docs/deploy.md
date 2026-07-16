# Deploy — passo a passo (quando o projeto GCP existir)

Checklist único para tirar o projeto do "código pronto" para "rodando na nuvem".

## 1. Projeto GCP (grátis)

1. Criar projeto no console GCP e anotar o `PROJECT_ID`.
2. BigQuery sandbox já vem ativo (10 GB storage + 1 TB query/mês, sem cartão).
3. Habilitar APIs: `run.googleapis.com`, `workflows.googleapis.com`,
   `cloudscheduler.googleapis.com`, `dataform.googleapis.com`, `artifactregistry.googleapis.com`,
   `secretmanager.googleapis.com`.

## 2. Ajustes no repo

- `workflow_settings.yaml` → trocar `CHANGE_ME_PROJECT_ID` pelo `PROJECT_ID`.
- Criar secret `dataform-github-token` no Secret Manager (token GitHub fine-grained,
  read-only no repo) — o Dataform usa pra ler este repositório.

## 3. Terraform

```bash
terraform -chdir=terraform init
terraform -chdir=terraform apply \
  -var project_id=SEU_PROJECT_ID \
  -var bucket_name=SEU_BUCKET_UNICO
```

Cria: bucket, datasets (bronze/silver/silver_spark/gold), tabelas externas, Artifact
Registry, Cloud Run Jobs, SAs + IAM, Dataform (repo/release/workflow config combinado
Silver+Gold), Cloud Workflow e Scheduler diário (07:00 BRT).

## 4. Primeira carga (bootstrap)

```bash
# build e push manual da imagem (o CD assume a partir do 2º deploy)
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
docker build -t southamerica-east1-docker.pkg.dev/PROJECT_ID/panorama-br/extractor:latest .
docker push southamerica-east1-docker.pkg.dev/PROJECT_ID/panorama-br/extractor:latest

# roda o pipeline inteiro uma vez
gcloud workflows run panorama-pipeline --location southamerica-east1
```

> Nota (lição de lakehouse): na primeira execução o release do Dataform pode ter sido
> compilado antes das tabelas Bronze existirem — se a invocation falhar, recompile o
> release no console do Dataform e dispare o `run-all` manualmente uma vez.

## 5. CI/CD

No GitHub do repo → Settings:
- Variables: `GCP_READY=true`
- Secrets: `GCP_PROJECT_ID`, `GCP_WIF_PROVIDER`, `GCP_SA_EMAIL`
  (Workload Identity Federation — sem chave JSON; ver `deploy.yml`)

## 6. Spark (Databricks Community)

1. Conta gratuita em community.cloud.databricks.com
2. Importar `spark/silver_rolling_stats.py` como notebook/job
3. Configurar `BRONZE_PATH` e `SILVER_SPARK_PATH` (gs://…) e agendar após o pipeline

## 7. Dashboard (Looker Studio)

Seguir `docs/dashboard.md` e colar o link público no README.
