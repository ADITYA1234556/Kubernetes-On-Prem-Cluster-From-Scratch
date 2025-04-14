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