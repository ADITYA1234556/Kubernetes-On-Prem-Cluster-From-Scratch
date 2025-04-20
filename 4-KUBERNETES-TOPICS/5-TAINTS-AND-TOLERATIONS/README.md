# TAINS AND TOLERATIONS
- Taints and Tolerations are a way to control which node can accept what and reject what.
- If a node can tolerate a taint from a pod, That pod can be scheduled on that node. 
- If a node has a taint of color=blue and a pod has a tolerate of color=white this pod cannot be scheduled on this node.
- If a node has a taint of color=blue and a pod has a tolerate of color=blue this pod can be scheduled on this node.
- To taint a node
```bash
k describe node node01
Taints:             <none>
k taint node node01 spray=mortein:NoSchedule
k describe node node01
Taints:             spray=mortein:NoSchedule
```
- To add toleration to a pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  labels:
    run: bee
  name: bee
spec:
  tolerations:
    - key: "spray"
      operator: "Equal"
      value: "mortein"
      effect: "NoSchedule"
  containers:
  - image: nginx
    name: bee
    resources: {}
  dnsPolicy: ClusterFirst
  restartPolicy: Always
status: {}
```
- To remove a taint from a node
```bash
kubectl taint node node01 spray=mortein:NoSchedule-
```