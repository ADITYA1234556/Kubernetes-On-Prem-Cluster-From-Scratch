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