# Spot Interruption Handling

Karpenter automatically drains nodes that receive a spot interruption
termination notice. Jobs should save work to durable storage and exit
gracefully when receiving the SIGTERM signal from Kubernetes.

For long running training jobs consider:

* Regular checkpointing to S3 or EFS
* Using a `preStop` hook to upload partial results
* Running pods with a `terminationGracePeriodSeconds` long enough to
  persist checkpoints
