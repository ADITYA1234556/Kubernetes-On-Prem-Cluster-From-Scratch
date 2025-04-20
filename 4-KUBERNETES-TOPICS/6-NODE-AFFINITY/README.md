# NODE AFFINITY
- Similar to Taints and Tolerations, Node Affinity is also used to tell the pods to be scheduled on particular node.
- Taints are explicitly protecting a node from unwanted pods.
- Node affinity is explicitly telling a pod to sit on a specific node.
- Tains are like a node saying avoid me
- Node affinity is like telling a pod to choose this node.
- To set NodeAffinity to a deployment or a pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd            
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
``` 
- Another way is to just check if Key exists
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: Exists    
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
```