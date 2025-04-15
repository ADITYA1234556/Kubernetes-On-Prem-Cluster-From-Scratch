- Create a python file
- Create virtual environment to install dependencies
```bash
sudo apt update
sudo apt install python3-venv python3-pip
python3 -m venv kubernetes
source kubernetes/bin/activate
pip install kubernetes
python3 main.py
```
- The main.py file will give us 3 files (k8s_namespaces.csv  k8s_nodes.csv  k8s_pods.csv) that has details about namespaces, pods, nodes. 