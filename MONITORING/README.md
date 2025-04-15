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

## Prometheus monitoring
- We can deploy prometheus using helm charts, <a href="https://helm.sh/docs/intro/install/">docs</a>
- Install helm
```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
helm version
```
- To install prometheus as helm chart
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install myprometheus prometheus-community/kube-prometheus-stack
```
- After deploying the chart
```bash
kubectl --namespace default get pods -l "release=myprometheus"
kubectl --namespace default get secrets myprometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo #Grafana password: prom-operator
```
- To access grafana, We will make it as type NodePort or LoadBalancer.
```bash
kubectl get svc
kubectl edit svc myprometheus-grafana
# or
kubectl expose service myprometheus-grafana --type=NodePort --target-port=80 --name=myprometheus-grafana-nodeport
#or 
kubectl patch svc myprometheus-grafana -p '{"spec": {"type": "NodePort"}}'
```
- To make prometheus send data to grafana
```bash
kubectl edit svc myprometheus-kube-promethe-prometheus # Change to NodePort to access prometheus UI
kubectl port-forward svc/myprometheus-kube-promethe-prometheus 9090:9090 & # run in background
```

## Adding more metrics to Promethues
- Expose the Prometheus State Metrics
```bash
kubectl patch svc myprometheus-kube-state-metrics -p '{"spec": {"type": "NodePort"}}'
# Engpoint http://192.168.56.21:31333/metrics of Prometheus State Metrics
```
- Edit the ConfigMap to add these additional metrics into prometheus
```bash
kubectl edit cm prometheus-server
```
## Custom Visualization in Grafana From Prometheus = Kube-state-Metrics
myprometheus-kube-state-metrics
expose the service -> access the UI -> http://svc-myprometheus-kube-state-metrics:NodePort/metrics
copy a query and paste it in grafana to monitor that query in Grafana as well
Also we can add the Chart ID 3662 that is Grafana visualization template used for monitoring kubernetes nodes.

- This that the helm chart for prometheus deploys:
1. Two statefulsets of Prometheus: 
    1. Actual core prometheus server managed by prometheus operator = -oper
    2. Alert manager statefuleset
2. Three deployments
    1. Prometheus
    2. Grafana
    3. Kube-state-metrics: scraps kubernetes component metrics. Health of deployments, pods, statefulsets
3. Three replicaset.
    1. Prometheus
    2. Grafana
    3. Kube-state-metrics: scraps kubernetes component metrics. Health of deployments, pods, statefulsets
4. Daemonset. To have one pod running in everynode. So a nodeexporter deamonset is running on all the server to collect metrics like CPU usage, Load on server, etc. and covert them so that prometheus and scrap and grafana can visualize. 
5. Configmaps
6. Secrets
7. Custom Resource Definitions (CRDs)

## Istio service mesh installation

```bash
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
helm install my-istio-base istio/base -n istio-system --create-namespace --wait
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null ||   kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
helm install istiod-chart istio/istiod -n istio-system
helm status istiod-chart -n istio-system
```
- To view the dashboard, install kiali
```bash
kubectl apply -f kiali.yml
```

### LoadBalancer for the Kubernetes cluster in AWS
Associate IAM OIDC provider to the cluster
eksctl utils associate-iam-oidc-provider --region eu-west-2 --cluster <your-cluster-name> --approve
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
aws eks describe-cluster --name mycluster --region eu-west-2   --query "cluster.roleArn" --output text # get role arn
Create IAM policy
```bash
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam-policy.json
```
Create IAM service account
```bash
eksctl create iamserviceaccount \
  --cluster <your-cluster-name> \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::<your-account-id>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```
Deploy Ingress LoadBalancer, First deploy Ingress controller. Without Ingress controller we cannot have Ingress or Ingress class.
Deploying Ingress controller as Helm chart
```bash
wget https://github.com/kubernetes/ingress-nginx/releases/download/helm-chart-4.11.5/ingress-nginx-4.11.5.tgz
mkdir ingresscontroller
tar -xvzf ingress-nginx-4.11.5.tgz
helm install ingresscontroller ingress-nginx/
helm list -A
helm status 
```
It may take a few minutes for the load balancer IP to be available.
You can watch the status by running 'kubectl get service --namespace default ingresscontroller-ingress-nginx-controller --output wide --watch'
Once ingress controller is deployed and a loadbalancer url can be seen, We can start deploying any number of ingress resources inside the cluster. 
Just make sure to annotate with the ingress class nginx. An ingress class with the name nginx would already have been deployed as a result of helm charts.
Look at ingress.yaml for a examply for ingress
If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:
```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: example-tls
    namespace: foo
  data:
    tls.crt: <base64 encoded cert>
    tls.key: <base64 encoded key>
  type: kubernetes.io/tls
```