# Manual Rollout Overrides

If automated analysis fails or metrics degrade, you can manually promote or abort the rollout.

## Pause or Resume Rollout
```
kubectl argo rollouts pause iris-rollout
kubectl argo rollouts resume iris-rollout
```

## Promote Immediately
```
kubectl argo rollouts promote iris-rollout
```

## Abort Rollout
```
kubectl argo rollouts abort iris-rollout
```
