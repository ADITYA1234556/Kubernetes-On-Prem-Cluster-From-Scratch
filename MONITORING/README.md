# Kubernetes

- Kubernetes runs with container runtime interface (CRI), either Docker or Container-D. That adheres to OCI(Open Container Initiative) standards. Docker or nerctl is the one recommended for production.

## Monitoring.
- In our kubernetes cluster we want to monitor node level metrics and pod level metrics for resource utilization like CPU, memory, etc.
- As of now, Kubernetes does not offer an built in solution. So we have to use open source solutions like Prometheus, Elasticstack, Datadog, Dynatrance.
- We can have metrics server per kubernetes cluster. The metrics server receieves metrics from each of the nodes, aggregrates them and stores them in memory.
- The metrics server is only an in-memory monitoring system and does not store it on the dist. As a result data is not persistent and we cannot see historical persistent data. So how are metrics collected by the metrics server?
- On each node, Kubernetes runs an agent **kubelet** which is responsible from kubernetes-api master server and running pods on the nodes. The **kubelet** also contains a sub component call the **cAdvisor** or container advisor which is responsible for receiving performance metrics from pods and sending it to **Kubelet** which will then send it to **kube-api** server and to **metrics server**
- To deploy the <a href="https://github.com/kubernetes-sigs/metrics-server">metrics server</a>
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl top node
kubectl top pod
```
- This will deploy pods, services, which acts as metrics server and polls for metrices from nodes in the cluster.
