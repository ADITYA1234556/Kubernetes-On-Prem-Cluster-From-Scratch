# Kubernetes
- In this repo, All major concepts of kubernetes mentioned.

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