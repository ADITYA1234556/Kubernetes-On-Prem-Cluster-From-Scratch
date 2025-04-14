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
- Output will be similar to this:
```bash
1761bef04e125165, started, controlplane01, https://192.168.56.11:2380, https://192.168.56.11:2379, false
d60f170a453bcaf4, started, controlplane02, https://192.168.56.12:2380, https://192.168.56.12:2379, false
```
- Reference: https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#starting-etcd-clusters