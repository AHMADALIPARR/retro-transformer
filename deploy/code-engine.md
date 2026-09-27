# Deploying `retro` on IBM Code Engine

Concise path from this repo to a running Code Engine job, plus how to wire
Cloud Object Storage (COS) for input/output artifacts.

## 0. Prerequisites

- [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) with the Code Engine plugin:
  `ibmcloud plugin install code-engine`
- A container registry namespace (IBM Container Registry used below).

```sh
ibmcloud login --sso            # or: ibmcloud login --apikey @keyfile
ibmcloud target -r us-south -g default
ibmcloud ce project create --name retro-transformer
# (if the project exists: ibmcloud ce project select --name retro-transformer)
```

## 1. Build and push the image

```sh
cd retro-transformer
ibmcloud cr namespace-add retro || true
docker build -f deploy/Dockerfile -t us.icr.io/retro/retro-transformer:latest .
docker push us.icr.io/retro/retro-transformer:latest
```

## 2. Create the job

Jobs are the right Code Engine primitive here: run-to-completion, one
COBOL file in, transformed files out.

```sh
ibmcloud ce job create --name retro-transform \
  --image us.icr.io/retro/retro-transformer:latest \
  --cpu 1 --memory 4G \
  --maxexecutiontime 600 \
  --env MOCK=1
```

## 3. Run it

Arguments after `--` become the container command (the image entrypoint is
`retro`):

```sh
# mock run, zero credentials
ibmcloud ce jobrun submit --job retro-transform -- \
  transform /data/HELLO.cbl --to java --mock

# live run against watsonx.ai (see "Going live" below)
ibmcloud ce jobrun submit --job retro-transform -- \
  transform /data/HELLO.cbl --to python
```

Fetch logs with `ibmcloud ce jobrun logs --job retro-transform`.

## 4. Going live with watsonx.ai

Store credentials as a Code Engine secret, then attach it to the job:

```sh
ibmcloud ce secret create --name wx-creds \
  --from-literal WATSONX_API_KEY='<ibm-cloud-api-key>' \
  --from-literal WATSONX_PROJECT_ID='<watsonx-project-id>'
ibmcloud ce job update --name retro-transform \
  --env-from-secret wx-creds \
  --env WATSONX_REGION=us-south \
  --env WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
```

With `WATSONX_API_KEY` set and no `--mock`, `retro` calls the real
watsonx.ai Granite model through `engine/`.

## 5. Wiring Cloud Object Storage

Recommended pattern: two buckets, `retro-in` and `retro-out`, synced by a
thin wrapper step around the job (Code Engine jobs have no persistent disk,
so artifacts must leave via COS).

```sh
# one-time setup
ibmcloud resource service-instance-create retro-cos \
  cloud-object-storage standard global
COS_ID=$(ibmcloud resource service-instance retro-cos --id -q)
ibmcloud cos bucket-create --bucket retro-in  --ibm-service-instance-id "$COS_ID"
ibmcloud cos bucket-create --bucket retro-out --ibm-service-instance-id "$COS_ID"
ibmcloud resource service-key-create retro-cos-key Manager \
  --instance-name retro-cos   # keep the HMAC / apikey it prints
```

Expose the bucket coordinates to the job:

```sh
ibmcloud ce job update --name retro-transform \
  --env COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud \
  --env COS_BUCKET_IN=retro-in \
  --env COS_BUCKET_OUT=retro-out
ibmcloud ce secret create --name cos-creds \
  --from-literal COS_APIKEY='<cos-hmac-or-iam-apikey>'
ibmcloud ce job update --name retro-transform --env-from-secret cos-creds
```

Then wrap each run: download `s3://retro-in/<file>.cbl` to `/data/`, run
`retro transform`, and upload `out/<program>/` to `s3://retro-out/<program>/`.
The `ibmcloud cos` CLI (or `rclone`) can do the sync in a pre/post step of
the same job spec, or in a second tiny job chained after it.

## Notes / limits

- Job max execution time caps long batch runs; split big COBOL estates
  into one jobrun per program (the engine already chunks per paragraph).
- `out/<program>/` is ephemeral inside the job — always upload to COS
  before the jobrun finishes.
- Keep `MOCK=1` for smoke tests; live Granite calls are billed per token.
