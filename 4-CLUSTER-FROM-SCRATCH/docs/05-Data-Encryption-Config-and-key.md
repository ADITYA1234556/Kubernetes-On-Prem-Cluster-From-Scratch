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
