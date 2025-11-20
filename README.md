# 🚀 Docling + Spark on ROSA

**Distributed PDF Structure Extraction on Kubernetes**

A production-ready system that combines [Docling](https://github.com/DS4SD/docling) (for PDF understanding) with [Apache Spark](https://spark.apache.org/) (for distributed computing) to process thousands of documents in parallel on **Red Hat OpenShift Service on AWS (ROSA)**.

---

## 📖 How It Works
1.  **Spark Operator** launches a Driver Pod.
2.  **Driver** distributes Docling code to Executor Pods.
3.  **Executors** process PDFs in parallel (OCR, Layout Analysis, Table Extraction).
4.  **Driver** collects results into a single `results.jsonl` file.
5.  **You** retrieve the results with a single command.

![Architecture Diagram](diagrams/Screenshot%202025-11-19%20at%209.35.21%E2%80%AFPM.png)

👉 **[Read the full Architecture & Concepts Guide (Conceptdocs.md)](./Conceptdocs.md)**

---

## ✅ Prerequisites

1.  **ROSA / OpenShift Cluster** (or any Kubernetes cluster).
2.  **Kubeflow Spark Operator** installed on the cluster (see guide below).
3.  **`oc`** or **`kubectl`** CLI configured.
4.  **Docker** (for building images).
5.  **Quay.io** account (or any container registry).

---

## 🛠️ Kubeflow Spark Operator Installation (ROSA)

If you haven't installed the Spark Operator yet, follow these steps to set it up on your ROSA cluster.

### 1. Prepare the Cluster
```bash
# Log in to your ROSA cluster
oc login

# Install Helm (if not already installed)
brew install helm

# Add the Spark Operator Helm repo
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update
```

### 2. Configure Permissions (SCC)
OpenShift requires specific permissions for the Spark Operator to run correctly.

Create a file named `spark-scc-rolebindings.yaml` with the following content:

```yaml
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: spark-nonroot
  namespace: kubeflow-spark-operator
subjects:
  - kind: ServiceAccount
    name: spark-operator-controller
    namespace: kubeflow-spark-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: 'system:openshift:scc:nonroot-v2'
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: spark-nonroot2
  namespace: kubeflow-spark-operator
subjects:
  - kind: ServiceAccount
    name: spark-operator-webhook
    namespace: kubeflow-spark-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: 'system:openshift:scc:nonroot-v2'
```

### 3. Install the Operator

```bash
# Create the namespace
oc new-project kubeflow-spark-operator

# Apply the SCC RoleBindings
oc apply -f spark-scc-rolebindings.yaml

# Install via Helm
helm install spark-operator spark-operator/spark-operator \
  --namespace kubeflow-spark-operator \
  --set webhook.enable=true \
  --set webhook.port=8080
```

### 4. Verify Installation
```bash
oc get pods -n kubeflow-spark-operator
# You should see spark-operator-controller and spark-operator-webhook running
```

---

## ⚡ Quick Start (Deploying the App)

### 1. Build & Push Image
Modify the `assets/` folder to include your PDFs, then build:

```bash
# Build for ROSA (Linux AMD64)
docker buildx build --platform linux/amd64 \
  -t quay.io/YOUR_USERNAME/docling-spark:latest \
  --push .
```

> **Note:** Update `k8s/docling-spark-app.yaml` with your image name (`quay.io/YOUR_USERNAME/...`).

### 2. Deploy to ROSA
This script handles Namespace, RBAC, SCC (Permissions), and Job Submission.

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

### 3. Retrieve Results
Wait for the job to finish (check logs). The driver will stay alive for 60 minutes.

```bash
# Copy results to your local machine
kubectl cp docling-spark-job-driver:/app/output/results.jsonl ./output/results.jsonl -n docling-spark

# View them
head -n 5 output/results.jsonl
```

### 4. Cleanup
```bash
kubectl delete sparkapplication docling-spark-job -n docling-spark
```

---

## 📂 Repository Structure

*   **`scripts/`**: Python source code.
    *   `docling_module/`: The PDF processing logic.
    *   `run_spark_job.py`: The Spark orchestration script.
*   **`k8s/`**: Kubernetes manifests.
    *   `docling-spark-app.yaml`: The Spark Job definition.
    *   `deploy.sh`: Deployment automation script.
*   **`assets/`**: Place your input PDFs here.
*   **`requirements.txt`**: Dependencies for **local development** (includes PySpark & macOS support).
*   **`requirements-docker.txt`**: Dependencies optimized for the **Docker container** (Linux only).
*   **`Conceptdocs.md`**: **Deep dive into architecture, decisions, and future roadmap.**

---

_See [Conceptdocs.md](./Conceptdocs.md) for the detailed roadmap._
