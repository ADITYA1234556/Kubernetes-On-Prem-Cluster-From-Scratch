import csv
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_k8s_details():
    # Load kubeconfig (uses default location ~/.kube/config)
    try:
        config.load_kube_config()  # Use load_incluster_config() if running inside a pod
    except Exception as e:
        print(f"Error loading kubeconfig: {e}")
        return

    # Create Kubernetes API clients
    v1_pods = client.CoreV1Api()
    v1_nodes = client.CoreV1Api()
    v1_namespaces = client.CoreV1Api()

    # Fetch pod details
    try:
        pod_list = v1_pods.list_pod_for_all_namespaces(watch=False)
        pod_details = []
        for pod in pod_list.items:
            pod_details.append({
                "Namespace": pod.metadata.namespace,
                "Pod Name": pod.metadata.name,
                "Status": pod.status.phase,
                "Node": pod.spec.node_name
            })
    except ApiException as e:
        print(f"Exception when fetching pods: {e}")
        pod_details = []

    # Fetch node details
    try:
        node_list = v1_nodes.list_node()
        node_details = []
        for node in node_list.items:
            node_details.append({
                "Node Name": node.metadata.name,
                "Status": node.status.conditions[-1].type,  # Assuming last condition is the status
                "Roles": node.metadata.labels.get("kubernetes.io/role", "N/A")
            })
    except ApiException as e:
        print(f"Exception when fetching nodes: {e}")
        node_details = []

    # Fetch namespace details
    try:
        namespace_list = v1_namespaces.list_namespace()
        namespace_details = []
        for namespace in namespace_list.items:
            namespace_details.append({
                "Namespace Name": namespace.metadata.name,
                "Status": namespace.status.phase
            })
    except ApiException as e:
        print(f"Exception when fetching namespaces: {e}")
        namespace_details = []

    return pod_details, node_details, namespace_details

def save_to_csv(pods, nodes, namespaces):
    # Save pod details to CSV
    with open('k8s_pods.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Namespace", "Pod Name", "Status", "Node"])
        writer.writeheader()
        writer.writerows(pods)

    # Save node details to CSV
    with open('k8s_nodes.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Node Name", "Status", "Roles"])
        writer.writeheader()
        writer.writerows(nodes)

    # Save namespace details to CSV
    with open('k8s_namespaces.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Namespace Name", "Status"])
        writer.writeheader()
        writer.writerows(namespaces)

def main():
    pods, nodes, namespaces = get_k8s_details()
    if pods:
        save_to_csv(pods, nodes, namespaces)
        print("Data has been saved to k8s_pods.csv, k8s_nodes.csv, and k8s_namespaces.csv.")
    else:
        print("Failed to retrieve Kubernetes resources.")

if __name__ == "__main__":
    main()

#python3 main.py