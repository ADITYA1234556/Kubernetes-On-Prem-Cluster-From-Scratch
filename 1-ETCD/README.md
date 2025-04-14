# ETCD
- ETCD is a **key** **value** pair **database** store where all information about the kubernetes cluster is stored. 
- Installing ETCD
1. Download Binaries
2. Extract it 
3. Run ETCD service
- ETCD runs on port 2379
- ETCD data store stores all information about the cluster like
1. Nodes
2. Pods
3. Configs
4. Secrets
5. Accounts
6. Roles
7. Bindings
8. All other
- When we run kubectl command, kube-api server gets the data from **ETCD** data store

## Setting up ETCD manually.
- If we setup our kubernetes from scratch we have to install ETCD binaries 
