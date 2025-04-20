# RESOURCE LIMITS
- Resource Limits are a way to specify how much a kubernetes object like namespace, pod, deploy, etc. can take resources from the cluster.
- We have Resource Request and Resource Limits for Memory and Cpu
- To force replace a pod
```bash
k replace --force -f /tmp/kubectl-edit-1925660770.yaml
```