# Manual Rollout Overrides

If automated analysis fails or metrics degrade, you can manually promote or abort the rollout.

## Pause or Resume Rollout
```bash
kubectl argo rollouts pause iris-rollout
kubectl argo rollouts resume iris-rollout
```

## Promote Immediately
```bash
kubectl argo rollouts promote iris-rollout
```

## Abort Rollout
```bash
kubectl argo rollouts abort iris-rollout
```
