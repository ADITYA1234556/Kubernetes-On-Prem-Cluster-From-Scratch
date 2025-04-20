## HIGH LEVEL PLAN TO DEPLOY THE CLUSTER
- We will start with deploying **ETCD** on the master nodes. 
- Then we will configure the control plane components: **apiserver**, **controller manager**, and **schedueler**
- Finally configure the **Loadbalancer**, we will use **HAPROXY** as the laodbalancer configuration.
- HAPROXY will listen on port 6443, and split all traffic to the **kubeapiserver**
- We will then point all nodes, and other components such as **kubectl** utility that needs access to the **kubeapiserver** to the **Loadbalancer**.
- So that if any of the master nodes fail, the loadbalancer can send the traffic to the other master node.