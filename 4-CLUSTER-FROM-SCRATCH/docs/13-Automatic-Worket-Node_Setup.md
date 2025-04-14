### Approach 2: Automatic certificate Signing using TLS bootstrap approach.
- By following TLS bootstrap approach the worker nodes can configure, renew and get the certificates signed by the CA by iteslf .
- We will see how we can bootstrap the second worker node using TLS bootstrap approach
- To simplify this, Consider we have one master and one worker node.
- There are two kinds of certificate configured on the worker node. 1. **Server certificate** and 2. **Client certificate**.
- In the **previous** method while configuring the **kubelet** for **worker 1**, we mentioned the paths of the server certificate for kubelet. Which is used by the clients to connect to the kubelet.
```bash
tlsCertFile: /var/lib/kubernetes/pki/${HOSTNAME}.crt
tlsPrivateKeyFile: /var/lib/kubernetes/pki/${HOSTNAME}.key
```
- So who is the client? And why would they connect to the **kubelet**?
- As of now, The kube-api server is the only client that connects to the **kubelet**. To monitor the status of the node, as well as to pull logs of pods running in the worker node when we run **kubectl logs podname**, or when we try to execute a command on the worker node using the **kubectl exec** command.
- In this **Approach2**, we dont have that certificates and we dont want to do that manually. 
- In the kubelet.service we also configured the kubeconfig file in worker1, the kubeconfig file has the client certificates which are responsible for authenticating with the kube-apiserver.
```bash
--kubeconfig=/var/lib/kubelet/kubelet.kubeconfig \\
```
- Our goal with TLS bootstrapping is to automate the certificate management so that the kubelet can take care of it by itself.
- All certificates requests are handled by the Administrative server which acts as the CA server. 
- To use the **Certificate servers api the kubelet has to authenticate iteself into the kubeapi server with the right set of permissions**.
- So we will **first create the right set of permissions on the master node** to allow this request from worker node 2.
- A special kind of authentication token, called bootstrap token can be created for this purpose. 
- Associate the token to a group called **system:bootstrappers**.
- We then configure the **kubelet** to use this token to authenticate with the kube-apiserver to the CA server.
- We can use the same token for all the worker nodes or create a seperate one for each worker node.

## What kind of permissions do these tokens have?
- The tokens initally will not have any permissions to it.
- So we will assign it certain permissions using roles, for it to have enough permissions to make certain api calls.
- A default cluster role exists for this purpose, called the **system:node-bootstrapper**
- This gives just enough permissions for the **kubelet** to csubmit a Certificate Signing request to the **API SERVER**.
- Once this role is assigned, the kubelet is able to generate a pair of certificates and submit the Certificate Signing request to the **KUBE API SERVER**.
- When we run the command
```bash
kubectl get csr
``` 
- We will see all the available Certificate Signing request and we have to manually approve it. Once approved the nodes will fetch the signed certificate and will join the cluster.
- But when we have many nodes as part of the cluster, It will become hard to approve this request. 
- So we can choose to allow these certificates to be automatically approved by attaching a another group called **cetificatesigningrequests:nodeclient**. With this role attached to the **system:node-bootstrapper** role, the CSR request gets approved automatically and the nodes can get the signed certificates and join the cluster.
- Once the nodes joins the cluster it becomes part of the **system:nodes** group and it no longer needs the **token**
- When the certificate expires, if we want the nodes to be able to renew certificates by itself then associate the cluster role **certificatesigningrequests:selfnodeclient** to the **system:nodes** group.

## Configuring the Kubelet
- Unlike manual process instead of specifyin tls certificates and kubeconfig we will mention the bootstrap config
- Manual kubelet service looked like this
```bash
tlsCertFile: /var/lib/kubernetes/pki/${HOSTNAME}.crt
tlsPrivateKeyFile: /var/lib/kubernetes/pki/${HOSTNAME}.key
--kubeconfig=/var/lib/kubelet/kubelet.kubeconfig \\
```
- Automatic kubelet service looked like this
```bash
--bootstrap-kubeconfig="/var/lib/kubelet/bootstrap-kubeconfig" \\
```

