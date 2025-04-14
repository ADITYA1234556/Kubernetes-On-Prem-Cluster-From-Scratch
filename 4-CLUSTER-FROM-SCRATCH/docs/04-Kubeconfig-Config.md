## Master Node Configuration for Kubeconfig file
- Kube config file is used by clients to access the kube-api-server. It has information about the API server and required credentials within it.
- The **admin user**, **Controller Manager**, **Scheduler**, **Kube-Proxy** are all clients to the kube-api server. So they all use **kubeconfig** files to communicate with the kube-api-server.
- We will see how to generate **kubeconfig** file for this purpose.

## Generating Kubernetes Configuration Files for Authentication
- In this section you will generate kubeconfig files for the **admin user**, **Controller Manager**, **Scheduler**, **Kube-Proxy**.
- Kubernetes Public IP Address: Each kubeconfig requires a Kubernetes API Server to connect to. 
- To support high availability the IP address assigned to the load balancer will be used, so let's first get the address of the loadbalancer into a shell variable such that we can use it in the kubeconfigs for services that run on worker nodes. 
- The admin user, controller manager and scheduler need to talk to the local API server, hence they use the localhost address.
- The **admin user**, **Controller Manager**, **Scheduler** can reach the api server using loopback address as they are in the master nodes.
- The **Kube-Proxy** will reach the master node using Loadbalancer IP.
```bash
LOADBALANCER=$(dig +short loadbalancer) #OP: 192.168.56.30
```

## The kube-proxy Kubernetes Configuration File
- Generate a kubeconfig file for the kube-proxy service: Note the --server address
```bash
# Preparing kube config file by creating kube-proxy.kubeconfig
kubectl config set-cluster kubernetes-the-hard-way \
--certificate-authority=/var/lib/kubernetes/pki/ca.crt \
--server=https://${LOADBALANCER}:6443 \
--kubeconfig=kube-proxy.kubeconfig

kubectl config set-credentials system:kube-proxy \
--client-certificate=/var/lib/kubernetes/pki/kube-proxy.crt \
--client-key=/var/lib/kubernetes/pki/kube-proxy.key \
--kubeconfig=kube-proxy.kubeconfig

kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=system:kube-proxy \
--kubeconfig=kube-proxy.kubeconfig
# Now make the kubeconfig as the data inside kube-proxy.kubeconfig
kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig
```

## The kube-controller-manager Kubernetes Configuration File
- Generate a kubeconfig file for the kube-controller-manager service: Note the --server address
```bash
# Preparing kube config file by creating kube-controller-manager.kubeconfig
kubectl config set-cluster kubernetes-the-hard-way \
--certificate-authority=/var/lib/kubernetes/pki/ca.crt \
--server=https://127.0.0.1:6443 \
--kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-credentials system:kube-controller-manager \
--client-certificate=/var/lib/kubernetes/pki/kube-controller-manager.crt \
--client-key=/var/lib/kubernetes/pki/kube-controller-manager.key \
--kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=system:kube-controller-manager \
--kubeconfig=kube-controller-manager.kubeconfig

kubectl config use-context default --kubeconfig=kube-controller-manager.kubeconfig
```

## The kube-scheduler Kubernetes Configuration File
- Generate a kubeconfig file for the kube-scheduler service: Note the --server address
```bash
# Preparing kube config file by creating kube-scheduler.kubeconfig
kubectl config set-cluster kubernetes-the-hard-way \
--certificate-authority=/var/lib/kubernetes/pki/ca.crt \
--server=https://127.0.0.1:6443 \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config set-credentials system:kube-scheduler \
--client-certificate=/var/lib/kubernetes/pki/kube-scheduler.crt \
--client-key=/var/lib/kubernetes/pki/kube-scheduler.key \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=system:kube-scheduler \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config use-context default --kubeconfig=kube-scheduler.kubeconfig
```

## The admin Kubernetes Configuration File
- Generate a kubeconfig file for the admin user: Note the --server address
```bash
# Preparing kube config file by creating admin.kubeconfig, NOTE: passing ca.crt
kubectl config set-cluster kubernetes-the-hard-way \
--certificate-authority=ca.crt \
--embed-certs=true \
--server=https://127.0.0.1:6443 \
--kubeconfig=admin.kubeconfig
# passing admin.crt and admin.key
kubectl config set-credentials admin \
--client-certificate=admin.crt \
--client-key=admin.key \
--embed-certs=true \
--kubeconfig=admin.kubeconfig

kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=admin \
--kubeconfig=admin.kubeconfig

kubectl config use-context default --kubeconfig=admin.kubeconfig
```

## Distribute the Kubernetes Configuration Files
- Now that we have created the Kubeconfig files for **admin user**, **Controller Manager**, **Scheduler**, **Kube-Proxy**.
- We will distribute kubeconfig file for **Kube-Proxy** to all the worker nodes.
- We will distribute kubeconfig file for **admin user**, **Controller Manager**, **Scheduler** to all the master nodes, as they are generated with loopback address 127.0.0.1.
- Copy the appropriate kube-proxy kubeconfig files to each worker instance:
```bash
for instance in node01 node02; do
  scp kube-proxy.kubeconfig ${instance}:~/
done
```
- Copy the appropriate admin.kubeconfig, kube-controller-manager and kube-scheduler kubeconfig files to each controller instance:
```bash
for instance in controlplane01 controlplane02; do
  scp admin.kubeconfig kube-controller-manager.kubeconfig kube-scheduler.kubeconfig ${instance}:~/
done
```

## Optional - Check kubeconfigs
- At controlplane01 and controlplane02 nodes, run the following, selecting option 2
```bash
./cert_verify.sh
# admin kubeconfig cert and key are correct
# /home/vagrant/kube-controller-manager.kubeconfig found
# /home/vagrant/kube-scheduler.kubeconfig found
```
**NOTE**: Worker nodes have **kubelet** and **kubeproxy**, we haven't generated certificates for **kubelet** yet. We will do it later.