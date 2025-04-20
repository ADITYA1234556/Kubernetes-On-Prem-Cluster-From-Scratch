# LABELS AND SELECTORS
- Labels and Selectors are a way to group objects. 
- Like a deployment is for Business Unit Payment, Tier Frontend
```bash
kubectl get pods --selector env=prod
kubectl get pods --selector env=prod | wc -l #word-count
kubectl get pods --selector env=prod --no-headers | wc -l #word-count
k get all --selector env=prod,bu=finance,tier=frontend #selects everything that has all these three labels
```
- Labels and selectors
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
   name: replicaset-1
spec:
   replicas: 2
   selector:
      matchLabels:
        env: prod
        bu: finance
        tier: frontend
   template:
     metadata:
       labels:
        tier: frontend
        env: prod
        bu: finance
     spec:
       containers:
       - name: nginx
         image: nginx
```