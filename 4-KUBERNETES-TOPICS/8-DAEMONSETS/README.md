# DAEMONSETS
- Daemonsets are pods that will be running on every node. One pod will be running on every node in the cluster.
- The use of Daemonsets is to maybe deploy a monitoring pod in all the nodes in the cluster.
- Like a prometheus Daemonset will deploy a pod on all the node, scrape metrics on every node.
- Kube-Proxy, Weave net are all deployed as Daemon Sets. 
- Kube-proxy will be present on each node to route traffic from pod to pod.
- Weave is a networking plugin that runs on every node to take care of networking.