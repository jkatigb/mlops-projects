# Steady State Metrics

The following Prometheus queries capture expected healthy behavior before and after chaos experiments:

- **Training job availability**
  ```
  sum(kube_pod_status_ready{pod=~"train-job-.*",condition="true"})
  ```
- **Inference service latency**
  ```
  histogram_quantile(0.90, rate(http_request_duration_seconds_bucket{job="inference"}[5m]))
  ```
- **S3 object integrity errors**
  ```
  rate(s3_corruption_total[5m])
  ```

Alerts can be configured to fire if these metrics breach predefined thresholds during chaos tests.
