## Verify the PKI Public Key Infrastructure
- PKI is all about trust. It helps verify who you are and ensures that data sent across a network hasn't been tampered with.
- Run the following, and select **option 1** to check all required certificates were generated.
```bash
./cert_verify.sh
```
- Expected output:
```bash
The selected option is 1, proceeding the certificate verification of Master node
ca cert and key found, verifying the authenticity
ca cert and key are correct
kube-apiserver cert and key found, verifying the authenticity
kube-apiserver cert and key are correct
kube-controller-manager cert and key found, verifying the authenticity
kube-controller-manager cert and key are correct
kube-scheduler cert and key found, verifying the authenticity
kube-scheduler cert and key are correct
service-account cert and key found, verifying the authenticity
service-account cert and key are correct
apiserver-kubelet-client cert and key found, verifying the authenticity
apiserver-kubelet-client cert and key are correct
etcd-server cert and key found, verifying the authenticity
etcd-server cert and key are correct
admin cert and key found, verifying the authenticity
admin cert and key are correct
kube-proxy cert and key found, verifying the authenticity
kube-proxy cert and key are correct
```
- If there are any errors, please review above steps and then re-verify

## Distribute the certificates
- Copy the appropriate certificates and private keys to each instance from the Administrative server where the certificates are held to all the **MASTER NODES**: 
```bash
for instance in controlplane01 controlplane02; do
  scp -o StrictHostKeyChecking=no ca.crt ca.key kube-apiserver.key kube-apiserver.crt \
    apiserver-kubelet-client.crt apiserver-kubelet-client.key \
    service-account.key service-account.crt \
    etcd-server.key etcd-server.crt \
    kube-controller-manager.key kube-controller-manager.crt \
    kube-scheduler.key kube-scheduler.crt \
    ${instance}:~/
done

for instance in node01 node02 ; do
  scp ca.crt kube-proxy.crt kube-proxy.key ${instance}:~/
done
```
- Optional - Check Certificates on controlplane02. At controlplane02 node run the following, selecting option 1
```bash
./cert_verify.sh
```