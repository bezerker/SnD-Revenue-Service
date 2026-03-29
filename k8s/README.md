# SnD Revenue Service Kubernetes Manifests

These manifests deploy a single-replica Discord bot process.

## Before apply

1. Edit `deployment.yaml` and set your published image.
2. Edit `configmap.yaml` with the target Discord `guild_id` and `audit_channel_id`.
3. Copy the template and fill in secrets (this repo gitignores `secret.local.yaml`):
   `cp k8s/secret.local.example.yaml k8s/secret.local.yaml`  
   Set `discord-token` and `openai-api-key` under `stringData` (plain text; the API server stores them encoded).

## Apply

```bash
kubectl apply -k k8s
```

## Verify

```bash
kubectl -n snd-revenue get pods
kubectl -n snd-revenue logs deploy/snd-revenue-service -f
```
