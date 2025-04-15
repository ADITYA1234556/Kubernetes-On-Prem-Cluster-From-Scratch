# Kubernetes
- In this repo, All major concepts of kubernetes mentioned.

## Steps
- Make sure you have passwordless conectivity to all the VMS, you can ssh-keygen copy id_rsa.pub to all the VMS .ssh/Authorized_keys
1. Install client tools **kubectl**
2. Provision Administrative server, 1 Administrative server per cluster which will act has Certificate Authority to issue certificates for Public Key Infrastructure.
3. Generate certificates for,
  1. Certificate Authority server: Who is responsible for signing all other certificates
  2. Server certificates
    1. Kube-apiserver
    2. Controller Manager
    3. Scheduler
    4. Admin certificates: For admin user who is part of the system:masters group
    5. ETCD certificate
    6. he API Server Kubelet Client Certificate: This certificate is for API server to authenticate with the kubelets when it requests information from them
    7. Service account
  3. Client certificates
    1. Kubelet: There are two ways to provision kubelet certificates. Manual way or TLS bootstrap. Requires creating roles.
    2. Kubeproxy
4. Distribute the certificates
  1. ca.crt kube-proxy.crt kube-proxy.key to the **worker** nodes
  2. ca.crt ca.key kube-apiserver.key kube-apiserver.crt apiserver-kubelet-client.crt apiserver-kubelet-client.key service-account.key service-account.crt etcd-server.key etcd-server.crt kube-controller-manager.key kube-controller-manager.crt kube-scheduler.key kube-scheduler.crt to the **master** nodes
5. Generate kubernetes configuration files for authentication:
  1. Kuber-proxy.config for Kuber-proxy
  2. Kube-controller-manager.config for Kube-controller
  3. Kube-scheduler.config for Kube-scheduler
  4. admin.config = for admin user
6. Distribute the certificates
  1. Kuber-proxy.config to the **worker** nodes
  2. Kube-controller-manager.config Kube-scheduler.config admin.config o the **worker** nodes
7. Generate the Data Encryption Config and Key: This keyy will be used to encrypt data at rest in the ETCD
8. Bootstrap ETCD server
9. Bootstrap Master nodes
10. Install Container Runtime Engine on worker nodes
11. Bootstrap the worker nodes
12. Configure the kubeconfig file that the kubectl utility will use for communication to api server.
13. Install pod networking
14. Create a ClusterRole to grant apiGroups to perform all operations on the resources namely {proxy, stats, log, spec, metrics} 
15. Install DNS solution for internal cluster communication
16. Smoke test the cluster
17. End-To-End tests inside the cluster.

## Troubleshooting.
## ISSUE 1:
- After bootstrapping my cluster with all the services, My kuberenets cluster was failing.
- Upo inspecting the logs of kube-apiserver **sudo journalctl -u kube-apiserver -f**.
- The issue was the file **encryption-config.yaml** mentioned in **/etc/systemd/system/kube-apiserver.service** was not present, I re-did the steps to create the encryption-config.yml and fixed.
```bash
"command failed" err="error while parsing file: error while loading file: error reading encryption provider configuration file \"/var/lib/kubernetes/encryption-config.yaml\": open /var/lib/kubernetes/encryption-config.yaml: no such file or directory"
```
- There was no encryption-config.yml file. That we mentioned to the kube-api
```bash
--encryption-provider-config=/var/lib/kubernetes/encryption-config.yaml \\
--kubelet-certificate-authority=/var/lib/kubernetes/pki/ca.crt \\
--kubelet-client-certificate=/var/lib/kubernetes/pki/apiserver-kubelet-client.crt \\
--kubelet-client-key=/var/lib/kubernetes/pki/apiserver-kubelet-client.key \\
--runtime-config=api/all=true \\
--service-account-key-file=/var/lib/kubernetes/pki/service-account.crt \\
--service-account-signing-key-file=/var/lib/kubernetes/pki/service-account.key \\
--service-account-issuer=https://${LOADBALANCER}:6443 \\
--service-cluster-ip-range=${SERVICE_CIDR} \\
--service-node-port-range=30000-32767 \\
--tls-cert-file=/var/lib/kubernetes/pki/kube-apiserver.crt \\
--tls-private-key-file=/var/lib/kubernetes/pki/kube-apiserver.key \\
```

## ISSUE 2: 
- My admin.kubeconfig didnt have current-context. So I was getting the error, 
```bash
E0414 14:21:52.766217   94661 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp 127.0.0.1:8080: connect: connection refused"
```
```yaml
    server: https://127.0.0.1:6443
  name: kubernetes-the-hard-way
contexts:
- context:
    cluster: kubernetes-the-hard-way
    user: admin
  name: default
current-context: ""
kind: Config
preferences: {}
users:
```

```bash
kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=admin \
--kubeconfig=admin.kubeconfig

kubectl config use-context default --kubeconfig=admin.kubeconfig
```
- After changes, **current-context** switched to default.
```yaml
    server: https://127.0.0.1:6443
  name: kubernetes-the-hard-way
contexts:
- context:
    cluster: kubernetes-the-hard-way
    user: admin
  name: default
current-context: default
kind: Config
preferences: {}
users:
```
- After fix, I was able to talk to kube-api server, Output:
```bash
kubectl get componentstatuses --kubeconfig admin.kubeconfig
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS    MESSAGE   ERROR
controller-manager   Healthy   ok
etcd-0               Healthy   ok
scheduler            Healthy   ok
```

## Issue 3: Namespace stuck termincating
1. Force deleting a namespace
```bash
kubectl get namespace istio-system -o json > istio-ns.json
vi istio-ns.json 
#    "spec": {
#        "finalizers": [
#            "kubernetes"
#        ]
#    },
#  ==> "spec": {} 
kubectl proxy --port=8001 # to open a proxy to talk to the API server.
curl -k -H "Content-Type: application/json" -X PUT --data-binary @istio-ns.json http://127.0.0.1:8001/api/v1/namespaces/istio-system/finalize
```