# STATIC PODS
- Static pods are pods that are created as a result of files present in /etc/kubernetes/manifests/
- The kubelet knows to create the pods. It get information from Kube-api server normally. 
- Also, it checks for a default directory that we mention in kubeler config.
- We can configure the kubelet to read pod definition files from a specific directory designated to store information about the pods.
- The kubelet periodically checks this path for the files and creates the pod if not already present.
- If we add or remove files from this directory the pods are added or created. 
- Either we pass in the /etc/systemd/system/kubelet.service of where this static pod directory location is.
- Or we pass this in cat /var/lib/kubelet/config.yaml