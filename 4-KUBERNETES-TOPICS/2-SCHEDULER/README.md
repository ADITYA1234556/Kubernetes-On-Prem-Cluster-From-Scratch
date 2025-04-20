# SCHEDULER
- Scheduler takes care of scheduling the pod, Once it gets confirmation from controller manager.
```bash
kubectl get pods -n kube-system
```
- If the scheduler is absent the pods wont be scheduled. The pod status will be in pending state.
- To manually schedule a pod, We specify the node name explicitly.
```yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  nodeName: node01
  containers:
  -  image: nginx
     name: nginx
```