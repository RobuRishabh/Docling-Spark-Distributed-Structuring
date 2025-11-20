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
OpenShift requires specific Security Context Constraints (SCC) for the Spark Operator to run correctly.

> **Note:** SCCs are OpenShift's way of controlling what permissions pods have (similar to Pod Security Standards in vanilla Kubernetes). The Spark Operator needs `nonroot-v2` SCC to run its containers with non-root user IDs.

The repository includes a pre-configured file `k8s/spark-scc-rolebindings.yaml` with the following content:

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

**What this does:** Grants the Spark Operator's service accounts permission to run containers as non-root users (UIDs > 0), which is required for the operator pods to start successfully on OpenShift.

### 3. Install the Operator

```bash
# Create the namespace
oc new-project kubeflow-spark-operator

# Apply the SCC RoleBindings
oc apply -f k8s/spark-scc-rolebindings.yaml

# Install via Helm with namespace watching configuration
helm install spark-operator spark-operator/spark-operator \
  --namespace kubeflow-spark-operator \
  --set webhook.enable=true \
  --set webhook.port=9443 \
  --set 'spark.jobNamespaces[0]=""'
```

> **Important:** The `spark.jobNamespaces[0]=""` setting tells the operator to watch **all namespaces** for `SparkApplication` resources. Without this, the operator won't detect jobs submitted to the `docling-spark` namespace.
> 
> **Alternative:** To watch only specific namespaces, use: `--set 'spark.jobNamespaces[0]=docling-spark'`
>
> **Zsh users:** If you get a "no matches found" error, use a values file instead:
> ```bash
> cat > /tmp/spark-values.yaml <<EOF
> spark:
>   jobNamespaces:
>     - ""
> webhook:
>   enable: true
>   port: 9443
> EOF
> 
> helm install spark-operator spark-operator/spark-operator \
>   --namespace kubeflow-spark-operator \
>   -f /tmp/spark-values.yaml
> ```

### 4. Verify Installation
```bash
oc get pods -n kubeflow-spark-operator
# You should see spark-operator-controller and spark-operator-webhook running
```

---

## ⚡ Quick Start (Deploying the App)

### 1. Choose Your Deployment Path

You have two options depending on your use case:

#### **Option A: Use Pre-Built Image (Recommended for Quick Start)**
The repository is pre-configured to use `quay.io/rishasin/docling-spark:latest`, which contains sample PDFs from the `assets/` directory. This allows you to **skip the build step entirely** and deploy immediately.

Proceed directly to Step 2 (Deploy to ROSA).

---

#### **Option B: Build Your Own Image (For Custom PDFs)**

**Best for:** Processing your own documents, customizing the application, or production deployments.

**Why you need this:** The `assets/` directory is copied into the Docker image at build time (see `Dockerfile` line 47). To process different PDFs, you must rebuild the image with your files.

**Steps:**

1. **Create the assets directory and add your PDFs:**
   ```bash
   mkdir -p assets
   cp /path/to/your/pdfs/*.pdf assets/
   ```

2. **Build the image for ROSA (Linux AMD64):**
   ```bash
   docker buildx build --platform linux/amd64 \
     -t quay.io/YOUR_USERNAME/docling-spark:latest \
     --push .
   ```
   
   > **Note:** The `--platform linux/amd64` flag ensures the image runs on ROSA nodes, even if you're building on Apple Silicon (M1/M2/M3 Mac).

3. **Update the Kubernetes manifest:**
   
   Edit `k8s/docling-spark-app.yaml` and change the image reference:
   ```yaml
   image: quay.io/YOUR_USERNAME/docling-spark:latest  # ← Update this line
   ```

4. **Proceed to Step 2** (Deploy to ROSA).

### 2. Deploy to ROSA
This script handles Namespace, RBAC, SCC (Permissions), and Job Submission.

```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

### 3. Retrieve Results
Wait for the job to finish (check logs). As soon as you see this is your terminal
```
🎉 ALL DONE!
✅ Enhanced processing complete!
😴 Sleeping for 60 minutes to allow file download...
   Run: kubectl cp docling-spark-job-driver:/app/output/results.jsonl ./output/results.jsonl -n docling-spark
```
Open another terminal and run the below command to save the results.

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
