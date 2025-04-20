# We will create kuberentes from scratch
- The vagrant file is written to create 5 node cluster with each 1gb cpu and 1gb ram.
- 2 worker nodes, 2 master nodes, 1 load balancer.
- Copy this vagrant file to your working directory, and run
```bash
vagrant up #pre-requisite vagrant and Virtualization enabled
```
- 5 vms should be spun up. Inside the hidden folder **.vagrant** we have private key. 
- ssh into the nodes
1. controlplane01 - 192.168.56.11 - vagrant
2. controlplane02 - 192.168.56.12 - vagrant
3. workernode01 - 192.168.56.21 - vagrant
4. workernode02 - 192.168.56.21 - vagrant

## Administrative client setup
- Now we set up one of the master nodes as **Administrative client** to perform administrative tasks, such as creating **certificates**, **kubeconfig** files and distributing it to other nodes in the cluster. 
- Setting up Administrative client server steps
```bash
ssh-keygen # To create certificates
cat .ssh/id_rsa.pub # Copy the contents and paste it in all nodes ..ssh/authorized_keys
# SSh into other nodes
cat >> ~/.ssh/authorized_keys <<-EOF
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDJ5T0Ni7OrY02XqI8Bp4KteTSFXZiGA8HSM8xGXuZAxFRKnNBTBxUkWIUegkLOnKk7yGubfJb8TAWjJlBVR9aliUAGPjVP1CZegCel1xY71Fsf1K3uk1kp1fo8771qJG/+Lk4eH47Q48tImkdiXRc2M7nqSkKa7PesMc9Lv9SUhHlIa9gdUid97uWKPM6kE9kdkKsAl///9vOkbgXt/NAEqUE31vEMUJ6/4WC+BrjSKewYPkgMOguvfl/Ji28gvzwCEt1usOtPs8I4g6YiZudR37Y+EciKex++0UKLjNpd97TCFLYavzc9dbmakJX3EOo9AX/IurFs34zxsJia1hsHk8DDR+NAH8yOAEcmxWYzSJTji+jX+SkEBkOa2eFBAc1fqf+B77EipIYUbVqikGDoT6VVNqDVTVAuBluDM5TMue2vZk9sPdwTXqJKSwUadMRbgU1Tnz4c1PDWbHVh3gl48TbCqsvGjB0WX5tE41YB/LAGs24oufUzzG7w7EKrOEE= vagrant@controlplane01
EOF
ssh controlplane02
ssh loadbalancer
ssh node01
ssh node02
######################################
#Install kubectl on administrative client
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
chmod +x kubectl
mkdir -p ~/.local/bin
mv ./kubectl ~/.local/bin/kubectl
kubectl version --client
```
- Now our Administrative client also one of the master node, is now able to securely connect to all the nodes of the cluster using **TLS** certificates.

## Provisioning the CA Certificate Authority and Generating TLS certificates.
- On the Administrative client server, we will provision it as CA Certificate Authority for managing TLS certificates. Run these commands to create a certificate on Administrative client server which is also one of the master node.
- We will provision a Certificate Authority that can be used to generate additional TLS certificates.
```bash
cat /etc/host # Make sure, during vagrant up all the nodes are named
# Set up environment variables. Run the following:
CONTROL01=$(dig +short controlplane01)
CONTROL02=$(dig +short controlplane02)
LOADBALANCER=$(dig +short loadbalancer)
SERVICE_CIDR=10.96.0.0/24
API_SERVICE=$(echo $SERVICE_CIDR | awk 'BEGIN {FS="."} ; { printf("%s.%s.%s.1", $1, $2, $3) }')
# Check that the environment variables are set. Run the following:
echo $CONTROL01
echo $CONTROL02
echo $LOADBALANCER
echo $SERVICE_CIDR
echo $API_SERVICE
```
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

## Master Node Configuration
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

## Generating the Data Encryption Config and Key
- In this part, we will generate **Data Encryption Config and Key**.
- Kubernetes stores all of this data about the cluster, applications and secrets in **ETCD DATA STORE**. 
- To store this data in an **Encrypted Format**, we must generate an **Encryption Key**.
- First we will create an **Encryption Key**. Next, we will create an **Encryption Config file**.
- Kubernetes stores a variety of data including cluster state, application configurations, and secrets. Kubernetes supports the ability to encrypt cluster data at rest, that is, the data stored within etcd.
- In this lab you will generate an encryption key and an encryption config suitable for encrypting Kubernetes Secrets.

## The Encryption Key
- Generate an encryption key. This is simply 32 bytes of random data, which we base64 encode:
```bash
ENCRYPTION_KEY=$(head -c 32 /dev/urandom | base64) #OP: +9d99uY1zwyaSqgTdLkzBA9vNlKDuo3KKL3pI7uzGeE
```

## Create Encryption config file
- Create the encryption-config.yaml encryption config file using the key create earlier:
```bash
cat > encryption-config.yaml <<-EOF
kind: EncryptionConfig
apiVersion: v1
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${ENCRYPTION_KEY}
      - identity: {}
EOF
```
- We will use this **Encryption config file** when we configure the **kube-api-server**

## Copy the encryption-config.yaml encryption config file to each master nodes:
```bash
for instance in controlplane01 controlplane02; do
  scp encryption-config.yaml ${instance}:~/
done
```

## Move encryption-config.yaml encryption config file to appropriate directory.
```bash
for instance in controlplane01 controlplane02; do
  ssh ${instance} sudo mkdir -p /var/lib/kubernetes/
  ssh ${instance} sudo mv encryption-config.yaml /var/lib/kubernetes/
done
```
- Reference: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/#encrypting-your-data

# KUBEADM or ClusterIp From Scratch

- For ClusterIP from scratch we need to download kuberentes release binaries and perform everything from scrath
- For kubeadm, these binaries are not required.

## WAY-1: KUBERNETES RELEASE BINARIES
- Kuberenetes releases different software versions, with every software version kubernetes builds and releases binaries and packages for different **operating systems**.
- Check the <a href="https://github.com/kubernetes/kubernetes/releases">kubernetes releases</a> page.
- Download the latest version to the system
```bash
https://github.com/kubernetes/kubernetes/archive/refs/tags/v1.32.3.tar.gz
tar -xvzf v1.32.3.tar.gz
ls 
kubernetes-1.32.3  v1.32.3.tar.gz
ls kubernetes-1.32.3/
CHANGELOG     CONTRIBUTING.md  LICENSES  OWNERS          README.md          SUPPORT.md  build    cmd                 docs    go.sum   go.work.sum  logo  plugin   test         vendor
CHANGELOG.md  LICENSE          Makefile  OWNERS_ALIASES  SECURITY_CONTACTS  api         cluster  code-of-conduct.md  go.mod  go.work  hack         pkg   staging  third_party
cd kubernetes-1.32.3/
./cluster/get-kube.sh 
# Will download kubernetes relase and binaries from actual server 
# Will download kubernetes-server-linux-amd64.tar.gz 
# will download and extract kubernetes.tar.gz as kbuernetes
```
- We should run a script that will download the appropriate binaries for our operating system.
```bash
cd kuberentes 
ls
LICENSES  README.md  client  cluster  docs  hack  platforms  server  version
./cluster/get-kube-binaries.sh 
```
- This downloads appropriate binaries for **Client** and **Server** components into their respective folders
- The client is automatically extracted and placed in the **client** directory
- The servers directory has all the master and control plane binaries. The binaries of **kubeadm**, **kube scheduler**, **contoller manager**, **kube-proxy**, **kubelet**, **kube-apiserver**, etc.
- These can be executed directly or configured as services on the Linux system.
- After running ./cluster/get-kube-binaries.sh it downloads appropriate binaries for **Client** and **Server** components into their respective folders.
```
ls client/
README  bin  kubernetes-client-linux-amd64.tar.gz

ls server/
README  kubernetes-manifests.tar.gz  kubernetes-server-linux-amd64.tar.gz
```
- To view <a href="https://kubernetes.io/releases/">Kubernetes Release Notes</a>

## HIGH LEVEL PLAN TO DEPLOY THE CLUSTER
- We will start with deploying **ETCD** on the master nodes. 
- Then we will configure the control plane components: **apiserver**, **controller manager**, and **schedueler**
- Finally configure the **Loadbalancer**, we will use **HAPROXY** as the laodbalancer configuration.
- HAPROXY will listen on port 6443, and split all traffic to the **kubeapiserver**
- We will then point all nodes, and other components such as **kubectl** utility that needs access to the **kubeapiserver** to the **Loadbalancer**.
- So that if any of the master nodes fail, the loadbalancer can send the traffic to the other master node.

## BOOTSTRAPPING THE ETCD CLUSTER
- We will deploy ETCD as a cluster.
- We will download the ETCD binary.

## Download and Install the etcd Binaries
- Remember to run the below commands on all the master nodes or all the servers that acts as ETCD data store, In this lab: controlplane01, and controlplane02
- Download the official etcd release binaries from the <a href="https://github.com/etcd-io/etcd">etcd</a> GitHub project.
```bash
mkdir etcd-binary
cd etcd-binary/
ETCD_VERSION="v3.5.9"
wget -q --show-progress --https-only --timestamping \
  "https://github.com/coreos/etcd/releases/download/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-${ARCH}.tar.gz"
```
- Extract and install the etcd server and the etcdctl command line utility:
```bash
tar -xvf etcd-${ETCD_VERSION}-linux-${ARCH}.tar.gz
sudo mv etcd-${ETCD_VERSION}-linux-${ARCH}/etcd* /usr/local/bin/
```

## Configure the etcd Server
- Copy and secure certificates. Note that we place ca.crt in our main PKI directory and link it from etcd to not have multiple copies of the cert lying around.
```bash
cd $HOME # where we have all the certificates {etcd-server.key etcd-server.crt ca.crt}
sudo mkdir -p /etc/etcd /var/lib/etcd /var/lib/kubernetes/pki
sudo cp etcd-server.key etcd-server.crt /etc/etcd/
sudo cp ca.crt /var/lib/kubernetes/pki/
sudo chown root:root /etc/etcd/*
sudo chmod 600 /etc/etcd/*
sudo chown root:root /var/lib/kubernetes/pki/*
sudo chmod 600 /var/lib/kubernetes/pki/*
sudo ln -s /var/lib/kubernetes/pki/ca.crt /etc/etcd/ca.crt
```
- To configure the ETCD, we need the internal IP address of the VMs.
- The instance internal IP address will be used to serve client requests and communicate with etcd cluster peers.
- Retrieve the internal IP address of the controlplane(etcd) nodes, and also that of controlplane01 and controlplane02 for the etcd cluster member list
```bash
CONTROL01=$(dig +short controlplane01)
CONTROL02=$(dig +short controlplane02)
echo $CONTROL01
echo $CONTROL02
```
- Each etcd member must have a unique name within an etcd cluster. 
- Set the etcd name to match the hostname of the current compute instance:
```bash
ETCD_NAME=$(hostname -s)
echo $ETCD_NAME
```
- Create the etcd.service systemd unit file:
```bash
cat <<-EOF | sudo tee /etc/systemd/system/etcd.service
[Unit]
Description=etcd
Documentation=https://github.com/coreos

[Service]
ExecStart=/usr/local/bin/etcd \\
  --name ${ETCD_NAME} \\
  --cert-file=/etc/etcd/etcd-server.crt \\
  --key-file=/etc/etcd/etcd-server.key \\
  --peer-cert-file=/etc/etcd/etcd-server.crt \\
  --peer-key-file=/etc/etcd/etcd-server.key \\
  --trusted-ca-file=/etc/etcd/ca.crt \\
  --peer-trusted-ca-file=/etc/etcd/ca.crt \\
  --peer-client-cert-auth \\
  --client-cert-auth \\
  --initial-advertise-peer-urls https://${PRIMARY_IP}:2380 \\
  --listen-peer-urls https://${PRIMARY_IP}:2380 \\
  --listen-client-urls https://${PRIMARY_IP}:2379,https://127.0.0.1:2379 \\
  --advertise-client-urls https://${PRIMARY_IP}:2379 \\
  --initial-cluster-token etcd-cluster-0 \\
  --initial-cluster controlplane01=https://${CONTROL01}:2380,controlplane02=https://${CONTROL02}:2380 \\
  --initial-cluster-state new \\
  --data-dir=/var/lib/etcd
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
cat /etc/systemd/system/etcd.service
```

## Start the etcd Server
```bash
sudo systemctl daemon-reload
sudo systemctl enable etcd
sudo systemctl start etcd
sudo systemctl status etcd
```

## Verification
- List the etcd cluster members.
- After running the above commands on both controlplane nodes, run the following on either or both of controlplane01 and controlplane02
```bash
sudo ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/etcd/ca.crt \
  --cert=/etc/etcd/etcd-server.crt \
  --key=/etc/etcd/etcd-server.key
```
- Output will be similar to this: Should list two ETCD servers as part of the cluster.
```bash
1761bef04e125165, started, controlplane01, https://192.168.56.11:2380, https://192.168.56.11:2379, false
d60f170a453bcaf4, started, controlplane02, https://192.168.56.12:2380, https://192.168.56.12:2379, false
```
- Reference: https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#starting-etcd-clusters

# Bootstrap Control Plane Components
- Now we will install Control plane components. 
- We will execute the tasks on both the master nodes for high availability.
- We will also create an external load balancer that exposes the Kubernetes API Servers to remote clients.
- The following components will be installed on each node: Kubernetes API Server, Scheduler, and Controller Manager.
- Note that in a production-ready cluster it is recommended to have an odd number of controlplane nodes as for multi-node services like etcd, leader election and quorum work better.

## Provision the Kubernetes Control Plane
- Download and Install the Kubernetes Controller Binaries, this will install binaries for **kube-apiserver**, **controller manager**, **scheduler** and **kubectl**
```bash
mkdir controlplanebootstrap
cd controlplanebootstrap/
KUBE_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)

wget -q --show-progress --https-only --timestamping \
  "https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kube-apiserver" \
  "https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kube-controller-manager" \
  "https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kube-scheduler" \
  "https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kubectl"
```
- Install the Kubernetes binaries and move them to /usr/local/bin/:
```bash
ls
kube-apiserver  kube-controller-manager  kube-scheduler  kubectl
chmod +x kube-apiserver kube-controller-manager kube-scheduler kubectl
sudo mv kube-apiserver kube-controller-manager kube-scheduler kubectl /usr/local/bin/
```
Reference: https://kubernetes.io/releases/download/#binaries

## Configure the Kubernetes API Server
- Place the key pairs, certificates and keys into the kubernetes data directory and secure. 
- Run these commands from the path where the certificates are stored.
```bash
cd $HOME
sudo mkdir -p /var/lib/kubernetes/pki

# Only copy CA keys as we'll need them again for workers.
sudo cp ca.crt ca.key /var/lib/kubernetes/pki
for c in kube-apiserver service-account apiserver-kubelet-client etcd-server kube-scheduler kube-controller-manager
do
sudo mv "$c.crt" "$c.key" /var/lib/kubernetes/pki/
done
sudo chown root:root /var/lib/kubernetes/pki/*
sudo chmod 600 /var/lib/kubernetes/pki/*
ls /var/lib/kubernetes/pki/                                               apiserver-kubelet-client.crt  etcd-server.crt     kube-controller-manager.crt  service-account.crt
apiserver-kubelet-client.key  etcd-server.key     kube-controller-manager.key  service-account.key
ca.crt                        kube-apiserver.crt  kube-scheduler.crt
ca.key                        kube-apiserver.key  kube-scheduler.key
```
- The instance internal IP address will be used to advertise the API Server to members of the cluster
- The load balancer IP address will be used as the external endpoint to the API servers.
- Retrieve these internal IP addresses:
- Loadbalancer
```bash
LOADBALANCER=$(dig +short loadbalancer)
```
- IP addresses of the two controlplane nodes, where the etcd servers are.
```bash
CONTROL01=$(dig +short controlplane01)
CONTROL02=$(dig +short controlplane02)
```
- Set the CIDR ranges used within the cluster
```bash
POD_CIDR=10.244.0.0/16
SERVICE_CIDR=10.96.0.0/16
```

## KUBE-API SERVER CONFIG
- Create the kube-apiserver.service systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kube-apiserver.service
[Unit]
Description=Kubernetes API Server
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-apiserver \\
  --advertise-address=${PRIMARY_IP} \\
  --allow-privileged=true \\
  --apiserver-count=2 \\
  --audit-log-maxage=30 \\
  --audit-log-maxbackup=3 \\
  --audit-log-maxsize=100 \\
  --audit-log-path=/var/log/audit.log \\
  --authorization-mode=Node,RBAC \\
  --bind-address=0.0.0.0 \\
  --client-ca-file=/var/lib/kubernetes/pki/ca.crt \\
  --enable-admission-plugins=NodeRestriction,ServiceAccount \\
  --enable-bootstrap-token-auth=true \\
  --etcd-cafile=/var/lib/kubernetes/pki/ca.crt \\
  --etcd-certfile=/var/lib/kubernetes/pki/etcd-server.crt \\
  --etcd-keyfile=/var/lib/kubernetes/pki/etcd-server.key \\
  --etcd-servers=https://${CONTROL01}:2379,https://${CONTROL02}:2379 \\
  --event-ttl=1h \\
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
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```
## Configure the Kubernetes Controller Manager
- Move the **kube-controller-manager kubeconfig** into place:
```bash
sudo mv kube-controller-manager.kubeconfig /var/lib/kubernetes/
```
- Create the kube-controller-manager.service systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kube-controller-manager.service
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-controller-manager \\
  --allocate-node-cidrs=true \\
  --authentication-kubeconfig=/var/lib/kubernetes/kube-controller-manager.kubeconfig \\
  --authorization-kubeconfig=/var/lib/kubernetes/kube-controller-manager.kubeconfig \\
  --bind-address=127.0.0.1 \\
  --client-ca-file=/var/lib/kubernetes/pki/ca.crt \\
  --cluster-cidr=${POD_CIDR} \\
  --cluster-name=kubernetes \\
  --cluster-signing-cert-file=/var/lib/kubernetes/pki/ca.crt \\
  --cluster-signing-key-file=/var/lib/kubernetes/pki/ca.key \\
  --controllers=*,bootstrapsigner,tokencleaner \\
  --kubeconfig=/var/lib/kubernetes/kube-controller-manager.kubeconfig \\
  --leader-elect=true \\
  --node-cidr-mask-size=24 \\
  --requestheader-client-ca-file=/var/lib/kubernetes/pki/ca.crt \\
  --root-ca-file=/var/lib/kubernetes/pki/ca.crt \\
  --service-account-private-key-file=/var/lib/kubernetes/pki/service-account.key \\
  --service-cluster-ip-range=${SERVICE_CIDR} \\
  --use-service-account-credentials=true \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

## Configure the Kubernetes Scheduler
- Move the kube-scheduler kubeconfig into place:
```bash
sudo mv kube-scheduler.kubeconfig /var/lib/kubernetes/
```
- Create the kube-scheduler.service systemd unit file
```bash
cat <<EOF | sudo tee /etc/systemd/system/kube-scheduler.service
[Unit]
Description=Kubernetes Scheduler
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-scheduler \\
  --kubeconfig=/var/lib/kubernetes/kube-scheduler.kubeconfig \\
  --leader-elect=true \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

## Secure kubeconfigs
```bash
sudo chmod 600 /var/lib/kubernetes/*.kubeconfig
```

### Optional - Check Certificates and kubeconfigs
- At controlplane01 and controlplane02 nodes, run the following, selecting option 3
```bash
./cert_verify.sh
```

## Start the Controller Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable kube-apiserver kube-controller-manager kube-scheduler
sudo systemctl start kube-apiserver kube-controller-manager kube-scheduler
sudo systemctl status kube-apiserver
sudo systemctl status kube-scheduler
sudo systemctl status kube-controller-manager
# Allow up to 10 seconds for the Kubernetes API Server to fully initialize.
```

## Verification
- After running the above commands on both controlplane nodes, run the following on controlplane01
```bash
kubectl get componentstatuses --kubeconfig admin.kubeconfig
```
- It will give you a deprecation warning here, but that's ok.
- Output:
```bash
kubectl get componentstatuses --kubeconfig admin.kubeconfig
Warning: v1 ComponentStatus is deprecated in v1.19+
NAME                 STATUS    MESSAGE   ERROR
controller-manager   Healthy   ok
etcd-0               Healthy   ok
scheduler            Healthy   ok
```

## CONFIGURING LOADBALANCER
- The Loadbalancer will route traffic to the kube-apiserver.
- We will use HAProxy Loadbalancer. So we will install HAProxy application on the instance dedicated for Loadbalancer.
- The kubernetes-the-hard-way static IP address will be attached to the resulting load balancer.

## Provision a Network Load Balancer
- A NLB operates at <a href="https://en.wikipedia.org/wiki/OSI_model#Layer_4:_Transport_layer">layer 4</a> (TCP) meaning it passes the traffic straight through to the back end servers unfettered and does not interfere with the TLS process, leaving this to the Kube API servers.
- Install HAProxy Loadbalancer in the VM.
```bash
sudo apt-get update && sudo apt-get install -y haproxy
``` 
- From the loadbalancer VM get the IP address of master nodes
```bash
CONTROL01=$(dig +short controlplane01)
CONTROL02=$(dig +short controlplane02)
LOADBALANCER=$(dig +short loadbalancer)
```
- Create HAProxy configuration to listen on API server port on this host and distribute requests evently to the two controlplane nodes.
- We configure it to operate as a <a href="https://en.wikipedia.org/wiki/Transport_layer">layer 4</a> loadbalancer (using mode tcp), which means it forwards any traffic directly to the backends without doing anything like <a href="https://www.ssl2buy.com/wiki/ssl-offloading">SSL offloading</a>.
```bash
cat <<EOF | sudo tee /etc/haproxy/haproxy.cfg
frontend kubernetes
    bind ${LOADBALANCER}:6443
    option tcplog
    mode tcp
    default_backend kubernetes-controlplane-nodes

backend kubernetes-controlplane-nodes
    mode tcp
    balance roundrobin
    option tcp-check
    server controlplane01 ${CONTROL01}:6443 check fall 3 rise 2
    server controlplane02 ${CONTROL02}:6443 check fall 3 rise 2
EOF
sudo systemctl restart haproxy
```

## Verification
- Make a HTTP request for the Kubernetes version info:
```bash
curl -k https://${LOADBALANCER}:6443/version
# This should output some details about the version and build information of the API server.
```
```json
{
  "major": "1",
  "minor": "32",
  "gitVersion": "v1.32.3",
  "gitCommit": "32cc146f75aad04beaaa245a7157eb35063a9f99",
  "gitTreeState": "clean",
  "buildDate": "2025-03-11T19:52:21Z",
  "goVersion": "go1.23.6",
  "compiler": "gc",
  "platform": "linux/amd64"
}
```

## INSTALLING CONTAINER RUNTIME ON THE NODES 
- To install the Container runtime, the commands below has to be installed on both the worker nodes.
- We will install **containerd** as the container run time for the worker nodes.
- Update the apt package index and install packages needed to use the Kubernetes apt repository:
```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
```
- Set up the required kernel modules and make them persistent
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```
- Set the required kernel parameters and make them persistent
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```
- Determine latest version of Kubernetes and store in a shell variable
```bash
KUBE_LATEST=$(curl -L -s https://dl.k8s.io/release/stable.txt | awk 'BEGIN { FS="." } { printf "%s.%s", $1, $2 }')
```
- Download the Kubernetes public signing key
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/${KUBE_LATEST}/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```
- Add the Kubernetes apt repository
```bash
sudo apt update
sudo apt-get install -y containerd kubernetes-cni kubectl ipvsadm ipset
```
- Configure the container runtime to use systemd Cgroups.

## BOOTSTRAPPING WORKER NODES SETUP
- After we have configured ETCD -> Master nodes with kube-apiserver, controller manager, scheduler. -> Loadbalancer.
- We can configure the worker nodes.
- If not done results in a controlplane that comes up, then all the pods start crashlooping. 
- kubectl will also fail with an error like The connection to the server x.x.x.x:6443 was refused - did you specify the right host or port?
- Create default configuration and pipe it through sed to correctly set Cgroup parameter.
```bash
sudo mkdir -p /etc/containerd
containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' | sudo tee /etc/containerd/config.toml
```
- Restart containerd
```bash
sudo systemctl restart containerd
```

## Two Approaches: Manual and Automatic
### Approach 1: Manual certificate Signing
- Generate Certificates for worker node manually and get it signed by CA server present in the Administrative server which is one per cluster.
- After getting it signed, we can get it to the worker node and configure the kubelet service to use this certificate.
- The problem is everytime the certificate expires we renew it by ourselves following this approach.
- We will now install the kubernetes components
1. kubelet
2. kube-proxy.

### Prerequisite
- The Certificates and Configuration are created on controlplane01 node and then copied over to workers using scp.
- Once this is done, the commands are to be run on first worker instance: node01
- Login to first worker instance using SSH Terminal.

### Provisioning Kubelet Client Certificates
- Kubernetes uses a special-purpose authorization mode called <a href="https://kubernetes.io/docs/reference/access-authn-authz/node/">Node Authorizer</a>, that specifically authorizes API requests made by Kubelets.
- In order to be authorized by the Node Authorizer, Kubelets must use a credential that identifies them as being in the system:nodes group, with a username of system:node:<nodeName>. In this section you will create a certificate for each Kubernetes worker node that meets the Node Authorizer requirements.
- Login to the Administrative server which acts as a CA server.
- Login to controlplane01, on controlplane01
```bash
NODE01=$(dig +short node01) # get ip address of worker node 01
```
```bash
cat > openssl-node01.cnf <<EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = node01
IP.1 = ${NODE01}
EOF

openssl genrsa -out node01.key 2048
openssl req -new -key node01.key -subj "/CN=system:node:node01/O=system:nodes" -out node01.csr -config openssl-node01.cnf
openssl x509 -req -in node01.csr -CA ca.crt -CAkey ca.key -CAcreateserial  -out node01.crt -extensions v3_req -extfile openssl-node01.cnf -days 1000
```
- We will get a **key** and **crt**
```bash
node01.key
node01.crt
```
### The kubelet Kubernetes Configuration File
- When generating kubeconfig files for Kubelets the client certificate matching the Kubelet's node name must be used.
- This will ensure Kubelets are properly authorized by the Kubernetes <a href="https://kubernetes.io/docs/reference/access-authn-authz/node/">Node Authorizer</a>.
- Get the kube-api server load-balancer IP.
```bash
LOADBALANCER=$(dig +short loadbalancer)
```
- Generate a kubeconfig file for the first worker node. From controlplane01:
```bash
kubectl config set-cluster kubernetes-the-hard-way \
--certificate-authority=/var/lib/kubernetes/pki/ca.crt \
--server=https://${LOADBALANCER}:6443 \
--kubeconfig=node01.kubeconfig

kubectl config set-credentials system:node:node01 \
--client-certificate=/var/lib/kubernetes/pki/node01.crt \
--client-key=/var/lib/kubernetes/pki/node01.key \
--kubeconfig=node01.kubeconfig

kubectl config set-context default \
--cluster=kubernetes-the-hard-way \
--user=system:node:node01 \
--kubeconfig=node01.kubeconfig

kubectl config use-context default --kubeconfig=node01.kubeconfig
# We will get a node01.kubeconfig file
```
### Copy certificates, private keys and kubeconfig files to the worker node:
- From controlplane01:
```bash
scp ca.crt node01.crt node01.key node01.kubeconfig node01:~/
```
### Download and Install Worker Binaries
- Now we have got all the certificates required from master node/ Adminsitrative server for worker node. 
- Now we will download and install the binaries for **kubelet** and **kube-proxy**
- From node01:
```bash
KUBE_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)

wget -q --show-progress --https-only --timestamping \
  https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kube-proxy \
  https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kubelet
```
- Reference: https://kubernetes.io/releases/download/#binaries
- Create the installation directories:
```bash
sudo mkdir -p \
  /var/lib/kubelet \
  /var/lib/kube-proxy \
  /var/lib/kubernetes/pki \
  /var/run/kubernetes
```
- Install the worker binaries:
```bash
chmod +x kube-proxy kubelet
sudo mv kube-proxy kubelet /usr/local/bin/
```
### Configure the Kubelet
- From node01, Copy keys and config to correct directories and secure:
```bash
sudo mv ${HOSTNAME}.key ${HOSTNAME}.crt /var/lib/kubernetes/pki/
sudo mv ${HOSTNAME}.kubeconfig /var/lib/kubelet/kubelet.kubeconfig
sudo mv ca.crt /var/lib/kubernetes/pki/
sudo mv kube-proxy.crt kube-proxy.key /var/lib/kubernetes/pki/
sudo chown root:root /var/lib/kubernetes/pki/*
sudo chmod 600 /var/lib/kubernetes/pki/*
sudo chown root:root /var/lib/kubelet/*
sudo chmod 600 /var/lib/kubelet/*
```
- Configure CIDR ranges used within the cluster:
```bash
POD_CIDR=10.244.0.0/16
SERVICE_CIDR=10.96.0.0/16
```
- Compute cluster DNS addess, which is conventionally .10 in the service CIDR range
```bash
CLUSTER_DNS=$(echo $SERVICE_CIDR | awk 'BEGIN {FS="."} ; { printf("%s.%s.%s.10", $1, $2, $3) }')
echo $CLUSTER_DNS
10.96.0.10

```
- Create the kubelet-config.yaml configuration file: Reference: https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/
```bash
cat <<EOF | sudo tee /var/lib/kubelet/kubelet-config.yaml
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: /var/lib/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
containerRuntimeEndpoint: unix:///var/run/containerd/containerd.sock
clusterDomain: cluster.local
clusterDNS:
  - ${CLUSTER_DNS}
cgroupDriver: systemd
resolvConf: /run/systemd/resolve/resolv.conf 
runtimeRequestTimeout: "15m"
tlsCertFile: /var/lib/kubernetes/pki/${HOSTNAME}.crt
tlsPrivateKeyFile: /var/lib/kubernetes/pki/${HOSTNAME}.key
registerNode: true
EOF
```
- The **resolvConf** configuration mentioned in "resolvConf: /run/systemd/resolve/resolv.conf" is used to avoid loops when using CoreDNS for service discovery on systems running systemd-resolved
- Create the kubelet.service systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kubelet.service
[Unit]
Description=Kubernetes Kubelet
Documentation=https://github.com/kubernetes/kubernetes
After=containerd.service
Requires=containerd.service

[Service]
ExecStart=/usr/local/bin/kubelet \\
  --config=/var/lib/kubelet/kubelet-config.yaml \\
  --kubeconfig=/var/lib/kubelet/kubelet.kubeconfig \\
  --node-ip=${PRIMARY_IP} \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```
## Configure the Kubernetes Proxy
- On node01:
```bash
sudo mv kube-proxy.kubeconfig /var/lib/kube-proxy/
```
- Create the kube-proxy-config.yaml configuration file. Reference: https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/
```bash
cat <<EOF | sudo tee /var/lib/kube-proxy/kube-proxy-config.yaml
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
clientConnection:
  kubeconfig: /var/lib/kube-proxy/kube-proxy.kubeconfig
mode: iptables
clusterCIDR: ${POD_CIDR}
EOF
```
- Create the kube-proxy.service systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kube-proxy.service
[Unit]
Description=Kubernetes Kube Proxy
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-proxy \\
  --config=/var/lib/kube-proxy/kube-proxy-config.yaml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```
### Optional - Check Certificates and kubeconfigs
- At node01 node, run the following, selecting option 4
```bash
./cert_verify.sh
```

### Start the Worker Services
- From node01: Remember to run the above commands on worker node: node01
```bash
sudo systemctl daemon-reload
sudo systemctl enable kubelet kube-proxy
sudo systemctl start kubelet kube-proxy
```

### Verification
- Now return to the controlplane01 node.
- List the registered Kubernetes nodes from the controlplane node:
```bash
kubectl get nodes --kubeconfig admin.kubeconfig
```

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


## We will start Bootstrapping the worker node 2 using TLS bootstrap approach
### Pre-Requisite
- kube-apiserver - Ensure bootstrap token based authentication is enabled on the kube-apiserver.
- run this command on controlplane01
```bash
grep 'enable-bootstrap-token-auth=true' /etc/systemd/system/kube-apiserver.service
#  --enable-bootstrap-token-auth=true \
```
- **kube-controller-manager** - The certificate requests are signed by the kube-controller-manager ultimately. 
- The kube-controller-manager requires the CA Certificate and Key to perform these operations.

### STEP 1: Create the Boostrap Token to be used by Nodes (Kubelets) to invoke Certificate API
- Run the following steps on controlplane01
- For the workers(kubelet) to access the Certificates API, they need to authenticate to the kubernetes api-server first.
- For this we create a <a href="https://kubernetes.io/docs/reference/access-authn-authz/bootstrap-tokens/">Bootstrap Token</a> to be used by the kubelet.
- Bootstrap Tokens take the form of a 6 character token id followed by 16 character token secret separated by a dot. Eg: abcdef.0123456789abcdef. More formally, they must match the regular expression [a-z0-9]{6}\.[a-z0-9]{16}
- Set an expiration date for the bootstrap token of 7 days from now (you can adjust this)
```bash
EXPIRATION=$(date -u --date "+7 days" +"%Y-%m-%dT%H:%M:%SZ") #2025-04-21T16:00:27Z - today date - 2024-04-14 7 days expiry
```
- Create **Bootstrap token** yaml file.
```bash
cat > bootstrap-token-07401b.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  # Name MUST be of form "bootstrap-token-<token id>"
  name: bootstrap-token-07401b
  namespace: kube-system

# Type MUST be 'bootstrap.kubernetes.io/token'
type: bootstrap.kubernetes.io/token
stringData:
  # Human readable description. Optional.
  description: "The default bootstrap token generated by 'kubeadm init'."

  # Token ID and secret. Required.
  token-id: 07401b
  token-secret: f395accd246ae52d

  # Expiration. Optional.
  expiration: ${EXPIRATION}

  # Allowed usages.
  usage-bootstrap-authentication: "true"
  usage-bootstrap-signing: "true"

  # Extra groups to authenticate the token as. Must start with "system:bootstrappers:"
  auth-extra-groups: system:bootstrappers:worker
EOF
```
- Create the token
```bash
kubectl create -f bootstrap-token-07401b.yaml --kubeconfig admin.kubeconfig
```
- Things to note:
1. expiration - make sure its set to a date in the future. The computed shell variable EXPIRATION ensures this.
2. auth-extra-groups - this is the group the worker nodes are part of. It must start with "system:bootstrappers:" This group does not exist already. This group is associated with this token.
- Once this is created the token to be used for authentication is 07401b.f395accd246ae52d
- Reference: https://kubernetes.io/docs/reference/access-authn-authz/bootstrap-tokens/#bootstrap-token-secret-format

### Step 2 Authorize nodes (kubelets) to create CSR
- Next we associate the group we created before to the system:node-bootstrapper ClusterRole. This ClusterRole gives the group enough permissions to bootstrap the kubelet
```bash
kubectl create clusterrolebinding create-csrs-for-bootstrapping \
  --clusterrole=system:node-bootstrapper \
  --group=system:bootstrappers \
  --kubeconfig admin.kubeconfig
```
--------------- OR ---------------
```bash
cat > csrs-for-bootstrapping.yaml <<EOF
# enable bootstrapping nodes to create CSR
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: create-csrs-for-bootstrapping
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:node-bootstrapper
  apiGroup: rbac.authorization.k8s.io
EOF


kubectl create -f csrs-for-bootstrapping.yaml --kubeconfig admin.kubeconfig
```
- Reference: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/#authorize-kubelet-to-create-csr

### Step 3 Authorize nodes (kubelets) to approve CSRs
```bash
kubectl create clusterrolebinding auto-approve-csrs-for-group \
  --clusterrole=system:certificates.k8s.io:certificatesigningrequests:nodeclient \
  --group=system:bootstrappers \
  --kubeconfig admin.kubeconfig
```
--------------- OR ---------------
```bash
cat > auto-approve-csrs-for-group.yaml <<EOF
# Approve all CSRs for the group "system:bootstrappers"
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: auto-approve-csrs-for-group
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:nodeclient
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl create -f auto-approve-csrs-for-group.yaml --kubeconfig admin.kubeconfig
```
- Reference: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/#approval

### Step 4 Authorize nodes (kubelets) to Auto Renew Certificates on expiration
- We now create the Cluster Role Binding required for the nodes to automatically renew the certificates on expiry.
- Note that we are NOT using the system:bootstrappers group here any more. 
- Since by the renewal period, we believe the node would be bootstrapped and part of the cluster already. All nodes are part of the system:nodes group.
```bash
kubectl create clusterrolebinding auto-approve-renewals-for-nodes \
  --clusterrole=system:certificates.k8s.io:certificatesigningrequests:selfnodeclient \
  --group=system:nodes \
  --kubeconfig admin.kubeconfig
```
--------------- OR ---------------
```bash
cat > auto-approve-renewals-for-nodes.yaml <<EOF
# Approve renewal CSRs for the group "system:nodes"
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: auto-approve-renewals-for-nodes
subjects:
- kind: Group
  name: system:nodes
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:selfnodeclient
  apiGroup: rbac.authorization.k8s.io
EOF


kubectl create -f auto-approve-renewals-for-nodes.yaml --kubeconfig admin.kubeconfig
```
- Reference: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/#approval

### Step 5 Configure the Binaries on the Worker node
- Going forward all activities are to be done on the node02 node until step11.
- Download and Install Worker Binaries
- Note that kubectl is required here to assist with creating the boostrap kubeconfigs for kubelet and kube-proxy
```bash
KUBE_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)

wget -q --show-progress --https-only --timestamping \
  https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kube-proxy \
  https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/${ARCH}/kubelet
```
- Reference: https://kubernetes.io/releases/download/#binaries
- Create the installation directories:
```bash
sudo mkdir -p \
  /var/lib/kubelet/pki \
  /var/lib/kube-proxy \
  /var/lib/kubernetes/pki \
  /var/run/kubernetes
```
- Install the worker binaries:
```bash
{
  chmod +x kube-proxy kubelet
  sudo mv kube-proxy kubelet /usr/local/bin/
}
```
- Move the certificates and secure them.
```bash
{
  sudo mv ca.crt kube-proxy.crt kube-proxy.key /var/lib/kubernetes/pki
  sudo chown root:root /var/lib/kubernetes/pki/*
  sudo chmod 600 /var/lib/kubernetes/pki/*
}
```

### Step 6 Configure Kubelet to TLS Bootstrap
- It is now time to configure the second worker to TLS bootstrap using the token we generated
- For `node01` we started by creating a kubeconfig file with the TLS certificates that we manually generated.
- Here, we don't have the certificates yet. So we cannot create a kubeconfig file. Instead we create a bootstrap-kubeconfig file with information about the token we created.
- This is to be done on the `node02` node. Note that now we have set up the load balancer to provide high availibilty across the API servers, we point kubelet to the load balancer.
- Set up some shell variables for nodes and services we will require in the following configurations:
```bash
LOADBALANCER=$(dig +short loadbalancer)
POD_CIDR=10.244.0.0/16
SERVICE_CIDR=10.96.0.0/16
CLUSTER_DNS=$(echo $SERVICE_CIDR | awk 'BEGIN {FS="."} ; { printf("%s.%s.%s.10", $1, $2, $3) }')
```
- Set up the bootstrap kubeconfig.
```bash
{
  sudo kubectl config --kubeconfig=/var/lib/kubelet/bootstrap-kubeconfig \
    set-cluster bootstrap --server="https://${LOADBALANCER}:6443" --certificate-authority=/var/lib/kubernetes/pki/ca.crt

  sudo kubectl config --kubeconfig=/var/lib/kubelet/bootstrap-kubeconfig \
    set-credentials kubelet-bootstrap --token=07401b.f395accd246ae52d

  sudo kubectl config --kubeconfig=/var/lib/kubelet/bootstrap-kubeconfig \
    set-context bootstrap --user=kubelet-bootstrap --cluster=bootstrap

  sudo kubectl config --kubeconfig=/var/lib/kubelet/bootstrap-kubeconfig \
    use-context bootstrap
}
```
--------------- OR ---------------
```bash
cat <<EOF | sudo tee /var/lib/kubelet/bootstrap-kubeconfig
apiVersion: v1
clusters:
- cluster:
    certificate-authority: /var/lib/kubernetes/pki/ca.crt
    server: https://${LOADBALANCER}:6443
  name: bootstrap
contexts:
- context:
    cluster: bootstrap
    user: kubelet-bootstrap
  name: bootstrap
current-context: bootstrap
kind: Config
preferences: {}
users:
- name: kubelet-bootstrap
  user:
    token: 07401b.f395accd246ae52d
EOF
```
- Reference: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/#kubelet-configuration

## Step 7 Create Kubelet Config File
- Create the `kubelet-config.yaml` configuration file:
Reference: https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/
```bash
cat <<EOF | sudo tee /var/lib/kubelet/kubelet-config.yaml
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
  x509:
    clientCAFile: /var/lib/kubernetes/pki/ca.crt
authorization:
  mode: Webhook
containerRuntimeEndpoint: unix:///var/run/containerd/containerd.sock
cgroupDriver: systemd
clusterDomain: "cluster.local"
clusterDNS:
  - ${CLUSTER_DNS}
registerNode: true
resolvConf: /run/systemd/resolve/resolv.conf
rotateCertificates: true
runtimeRequestTimeout: "15m"
serverTLSBootstrap: true
EOF
```
- Note: We are not specifying the certificate details - tlsCertFile and tlsPrivateKeyFile - in this file

## Step 8 Configure Kubelet Service
Create the `kubelet.service` systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kubelet.service
[Unit]
Description=Kubernetes Kubelet
Documentation=https://github.com/kubernetes/kubernetes
After=containerd.service
Requires=containerd.service

[Service]
ExecStart=/usr/local/bin/kubelet \\
  --bootstrap-kubeconfig="/var/lib/kubelet/bootstrap-kubeconfig" \\
  --config=/var/lib/kubelet/kubelet-config.yaml \\
  --kubeconfig=/var/lib/kubelet/kubeconfig \\
  --cert-dir=/var/lib/kubelet/pki/ \\
  --node-ip=${PRIMARY_IP} \\
  --v=2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```
- Things to note here:
- **bootstrap-kubeconfig**: Location of the bootstrap-kubeconfig file.
- **cert-dir**: The directory where the generated certificates are stored.
- **kubeconfig**: We specify a location for this *but we have not yet created it*. Kubelet will create one itself upon successful bootstrap.

## Step 9 Configure the Kubernetes Proxy
In one of the previous steps we created the kube-proxy.kubeconfig file. Check [here](https://github.com/mmumshad/kubernetes-the-hard-way/blob/master/docs/05-kubernetes-configuration-files.md) if you missed it.
```bash
{
  sudo mv kube-proxy.kubeconfig /var/lib/kube-proxy/
  sudo chown root:root /var/lib/kube-proxy/kube-proxy.kubeconfig
  sudo chmod 600 /var/lib/kube-proxy/kube-proxy.kubeconfig
}
```
- Create the `kube-proxy-config.yaml` configuration file:

- Reference: https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/
```bash
cat <<EOF | sudo tee /var/lib/kube-proxy/kube-proxy-config.yaml
kind: KubeProxyConfiguration
apiVersion: kubeproxy.config.k8s.io/v1alpha1
clientConnection:
  kubeconfig: /var/lib/kube-proxy/kube-proxy.kubeconfig
mode: iptables
clusterCIDR: ${POD_CIDR}
EOF
```
- Create the `kube-proxy.service` systemd unit file:
```bash
cat <<EOF | sudo tee /etc/systemd/system/kube-proxy.service
[Unit]
Description=Kubernetes Kube Proxy
Documentation=https://github.com/kubernetes/kubernetes

[Service]
ExecStart=/usr/local/bin/kube-proxy \\
  --config=/var/lib/kube-proxy/kube-proxy-config.yaml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

## Step 10 Start the Worker Services
- On `node02`:
```bash
{
  sudo systemctl daemon-reload
  sudo systemctl enable kubelet kube-proxy
  sudo systemctl start kubelet kube-proxy
}
```
- Remember to run the above commands on worker node: `node02`
### Optional - Check Certificates and kubeconfigs
- At `node02` node, run the following, selecting option 5
[//]: # (command:sleep 5)
[//]: # (command:./cert_verify.sh 5)
```
./cert_verify.sh
```
## Step 11 Approve Server CSR
- Now, go back to `controlplane01` and approve the pending kubelet-serving certificate
[//]: # (host:controlplane01)
[//]: # (command:sudo apt install -y jq)
[//]: # (command:. ./approve-csr.sh)
```bash
kubectl get csr --kubeconfig admin.kubeconfig
```
- Output - Note the name will be different, but it will begin with `csr-`
```
NAME        AGE   SIGNERNAME                                    REQUESTOR                 REQUESTEDDURATION   CONDITION
csr-7k8nh   85s   kubernetes.io/kubelet-serving                 system:node:node02        <none>              Pending
csr-n7z8p   98s   kubernetes.io/kube-apiserver-client-kubelet   system:bootstrap:07401b   <none>              Approved,Issued
```
- Approve the pending certificate. Note that the certificate name `csr-7k8nh` will be different for you, and each time you run through.
```
kubectl certificate approve --kubeconfig admin.kubeconfig csr-7k8nh
```
- Note: In the event your cluster persists for longer than 365 days, you will need to manually approve the replacement CSR.

- Reference: https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/#kubectl-approval

## Verification
- List the registered Kubernetes nodes from the controlplane node:

```bash
kubectl get nodes --kubeconfig admin.kubeconfig
```

Output will be similar to

```
NAME       STATUS      ROLES    AGE   VERSION
node01     NotReady    <none>   93s   v1.28.4
node02     NotReady    <none>   93s   v1.28.4
```
Nodes are still not yet ready. As previously mentioned, this is expected.
Next: [Configuring Kubectl](./12-configuring-kubectl.md)</br>
Prev: [Bootstrapping the Kubernetes Worker Nodes](./10-bootstrapping-kubernetes-workers.md)