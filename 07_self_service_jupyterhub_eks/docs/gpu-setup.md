# GPU Setup Guide for JupyterHub

This guide covers GPU configuration and usage in JupyterHub on EKS.

## GPU Node Configuration

### Node Types
The deployment uses AWS G4dn instances with NVIDIA T4 GPUs:
- `g4dn.xlarge`: 1 GPU, 4 vCPUs, 16 GB RAM
- `g4dn.2xlarge`: 1 GPU, 8 vCPUs, 32 GB RAM

### Scaling Configuration
GPU nodes are configured to scale from 0 to 5 instances based on demand.

## Using GPU in JupyterHub

### 1. Select GPU Profile
When spawning a notebook, select the "GPU environment (1x Tesla T4)" profile.

### 2. Verify GPU Access
```python
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

### 3. Monitor GPU Usage
```python
!nvidia-smi
```

## GPU Libraries

The GPU profile includes pre-installed libraries:
- PyTorch with CUDA support
- TensorFlow with GPU support
- CUDA toolkit
- cuDNN

### Installing Additional Libraries
```bash
# In a notebook cell
!pip install transformers accelerate
!pip install jax[cuda]
```

## Best Practices

### 1. Resource Management
- Always clear GPU memory after use:
  ```python
  torch.cuda.empty_cache()
  ```

### 2. Efficient Batch Sizes
- Start with smaller batch sizes and increase gradually
- Monitor GPU memory usage with `nvidia-smi`

### 3. Mixed Precision Training
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    output = model(input)
    loss = criterion(output, target)
```

### 4. Multi-GPU Training
For distributed training across multiple GPUs (if available):
```python
import torch.distributed as dist
dist.init_process_group(backend='nccl')
```

## Troubleshooting

### GPU Not Available
1. Check if you selected the GPU profile
2. Verify node availability:
   ```bash
   kubectl get nodes -l workload=gpu
   ```

### Out of Memory Errors
1. Reduce batch size
2. Use gradient accumulation
3. Enable mixed precision training

### Performance Issues
1. Check GPU utilization: `nvidia-smi`
2. Profile your code:
   ```python
   torch.cuda.synchronize()
   start = time.time()
   # Your code here
   torch.cuda.synchronize()
   print(f"Time: {time.time() - start:.2f}s")
   ```

## Cost Optimization

### 1. Use Spot Instances
GPU nodes use spot instances by default for 60-90% cost savings.

### 2. Enable Auto-shutdown
Notebooks automatically shut down after 1 hour of inactivity.

### 3. Right-size Workloads
Use CPU profiles for data preparation and GPU only for training.

### 4. Schedule Long Jobs
For training jobs > 2 hours, consider using AWS Batch or SageMaker.