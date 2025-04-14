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

