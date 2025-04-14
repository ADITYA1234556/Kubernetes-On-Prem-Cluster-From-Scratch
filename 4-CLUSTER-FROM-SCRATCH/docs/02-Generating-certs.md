## Certificate Authority - Create certificates for certificate authority
- Create a CA certificate by first creating a private key, then using it to create a certificate signing request, then self-signing the new certificate with our key.
- The Certificate Authority is responsible for all certificate management in the system.
```bash
# Create private key for CA
openssl genrsa -out ca.key 2048 # Gives a private key ca.key
# Create Certificate Signing Rquest using the private key for the name KUBERNETES-CA
openssl req -new -key ca.key -subj "/CN=KUBERNETES-CA/O=Kubernetes" -out ca.csr # gives ca.csr
# Self sign the csr using its own private key and Certificate Signing Request
openssl x509 -req -in ca.csr -signkey ca.key -CAcreateserial -out ca.crt -days 1000 # gives a cert
# Now we have three files ca.crt, ca.csr, ca.key. We can ignore the ca.csr file
```
## The Admin Client Certificate - Create ceritifcates for cluster admin
- Generate the admin client certificate and private key. All certificates created from this point, should be signed by Certificate Authority to be valid inside the cluster.
```bash
# Generate private key for admin user
openssl genrsa -out admin.key 2048
# Generate Certificate Signing Rquest for admin user. Note the OU. With the name admin and group name as system:masters
openssl req -new -key admin.key -subj "/CN=admin/O=system:masters" -out admin.csr
# Sign certificate for admin user using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out admin.crt -days 1000
```
## The Controller Manager Client Certificate - Create ceritifcates for Controller Manager
```bash
# Generate private key for Controller Manager
openssl genrsa -out kube-controller-manager.key 2048
# Generate Certificate Signing Rquest for controller Manager. Note the OU. With the name Controller Manager and group name as system:kube-controller-manager
openssl req -new -key kube-controller-manager.key \
-subj "/CN=system:kube-controller-manager/O=system:kube-controller-manager" -out kube-controller-manager.csr
# Sign certificate for Controller Manager using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in kube-controller-manager.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out kube-controller-manager.crt -days 1000
```
## The Kube Proxy Client Certificate - Create ceritifcates for Kube Proxy
```bash
# Generate private key for Kube Proxy
openssl genrsa -out kube-proxy.key 2048
# Generate Certificate Signing Rquest for Kube Proxy. Note the OU. With the name Kube Proxy and group name as system:node-proxier
openssl req -new -key kube-proxy.key \
-subj "/CN=system:kube-proxy/O=system:node-proxier" -out kube-proxy.csr
# Sign certificate for Kube Proxy using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in kube-proxy.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out kube-proxy.crt -days 1000
```
## The Scheduler Client Certificate - Create ceritifcates for Scheduler
```bash
# Generate private key for Scheduler
openssl genrsa -out kube-scheduler.key 2048
# Generate Certificate Signing Rquest for Scheduler. Note the OU. With the name kube-scheduler and group name as system:kube-scheduler
openssl req -new -key kube-scheduler.key \
-subj "/CN=system:kube-scheduler/O=system:kube-scheduler" -out kube-scheduler.csr
# Sign certificate for kube-scheduler using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in kube-scheduler.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out kube-scheduler.crt -days 1000
```

## The API Server Kubelet Client Certificate
- This certificate is for the API server to authenticate with the KUBELETES when it requests information from them
- The openssl command cannot take alternate names as command line parameter. So we must create a conf file for it:
```bash
cat > openssl-kubelet.cnf <<-EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = critical, CA:FALSE
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF
```
- Generate certs for kubelet authentication
```bash
# Generate private key for kubelet
openssl genrsa -out apiserver-kubelet-client.key 2048
# Generate Certificate Signing Rquest for kubelet. Note the OU. With the name kube-apiserver-kubelet-client and group name as system:masters. ALSO we are passing openssl-kubelet.cnf while creating CSR
openssl req -new -key apiserver-kubelet-client.key \
-subj "/CN=kube-apiserver-kubelet-client/O=system:masters" -out apiserver-kubelet-client.csr -config openssl-kubelet.cnf
# Sign certificate for kubelet, along with openssl-kubelet.cnf using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in apiserver-kubelet-client.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out apiserver-kubelet-client.crt -extensions v3_req -extfile openssl-kubelet.cnf
```

## The Kubernetes API Server Certificate
- The kube-apiserver certificate requires all names that kube-api server goes by so that various components may reach it with its alternate names.
- These include the different DNS names, and IP addresses such as the controlplane servers IP address, the load balancers IP address, the kube-api service IP address etc. 
- These provide an identity for the certificate, which is key in the SSL process for a server to prove who it is.
- The openssl command cannot take alternate names as command line parameter. So we must create a conf file for it:
```bash
cat > openssl.cnf <<-EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = critical, CA:FALSE
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster
DNS.5 = kubernetes.default.svc.cluster.local
IP.1 = ${API_SERVICE}
IP.2 = ${CONTROL01}
IP.3 = ${CONTROL02}
IP.4 = ${LOADBALANCER}
IP.5 = 127.0.0.1
EOF
```
- Now generate Certificates by passing this openssl.cnf file
```bash
# Generate private key for Kubernetes API Server
openssl genrsa -out kube-apiserver.key 2048
# Generate Certificate Signing Rquest for Kubernetes API Server. Note the OU. With the name Kubernetes API Server and group name as Kubernetes. ALSO we are passing OPENSSL.CNF while creating CSR
openssl req -new -key kube-apiserver.key \
-subj "/CN=kube-apiserver/O=Kubernetes" -out kube-apiserver.csr -config openssl.cnf
# Sign certificate for Kubernetes API Server, along with OPENSSL.CNF using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in kube-apiserver.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out kube-apiserver.crt -extensions v3_req -extfile openssl.cnf -days 1000
```

## The ETCD Server Certificate
- Similarly ETCD server certificate must have addresses of all the servers part of the ETCD cluster. Similarly, this is a server certificate, which is again all about proving identity.
- The openssl command cannot take alternate names as command line parameter. So we must create a conf file for it:
```bash
cat > openssl-etcd.cnf <<-EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
IP.1 = ${CONTROL01}
IP.2 = ${CONTROL02}
IP.3 = 127.0.0.1
EOF
```
- Generates certs for ETCD
```bash
# Generate private key for ETCD
openssl genrsa -out etcd-server.key 2048
# Generate Certificate Signing Rquest for ETCD. Note the OU. With the name etcd-server and group name as Kubernetes. ALSO we are passing openssl-etcd.cnf while creating CSR
openssl req -new -key etcd-server.key \
-subj "/CN=etcd-server/O=Kubernetes" -out etcd-server.csr -config openssl-etcd.cnf
# Sign certificate for ETCD, along with openssl-etcd.cnf using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in etcd-server.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out etcd-server.crt -extensions v3_req -extfile openssl-etcd.cnf -days 1000
```

## The Service Account Key Pair
- The Kubernetes Controller Manager leverages a key pair to generate and sign service account tokens as described in the <a href="https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/">managing service accounts</a> documentation.
- Generate the service-account certificate and private key:
```bash
# Generate private key for Service Account
openssl genrsa -out service-account.key 2048
# Generate Certificate Signing Rquest for Service Account. Note the OU. With the name Service Account and group name as Kubernetes. 
openssl req -new -key service-account.key \
-subj "/CN=service-accounts/O=Kubernetes" -out service-account.csr
# Sign certificate for Service Account using Certificate Authority servers private key and Certificate that is valid for 1000 days
openssl x509 -req -in service-account.csr \
-CA ca.crt -CAkey ca.key -CAcreateserial -out service-account.crt -days 1000
```

## Certificates for Kubelet will be done later
