# Kubeflow Spark Operator on OpenShift

This documentation details how the Kubeflow Spark Operator works on OpenShift, its architecture, installation, and how to run a distributed Spark workload using the `docling` library.

## 1. SparkApplication CRD

The **SparkApplication** Custom Resource Definition (CRD) is the core abstraction provided by the operator. It allows you to define Spark applications declaratively using Kubernetes YAML manifests, similar to how you define Deployments or Pods.

Key fields in the `SparkApplication` spec include:

*   **`type`**: The language of the application (`Python`).
*   **`mode`**: Deployment mode (`cluster` or `client`). In `cluster` mode, the driver runs in a pod.
*   **`image`**: The container image to use for the driver and executors.
*   **`mainApplicationFile`**: The entry point path (e.g., `local:///app/scripts/run_spark_job.py`).
*   **`sparkVersion`**: The version of Spark to use (must match the image).
*   **`restartPolicy`**: Handling of failures (`Never`, `OnFailure`, `Always`).
*   **`driver` / `executor`**: Resource requests (cores, memory), labels, and service accounts for the driver and executor pods.

Example snippet from `k8s/docling-spark-app.yaml`:

```yaml
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: docling-spark-job
spec:
  type: Python
  mode: cluster
  image: quay.io/rishasin/docling-spark:latest
  mainApplicationFile: local:///app/scripts/run_spark_job.py
  driver:
    cores: 1
    memory: "4g"
    serviceAccount: spark-driver
  executor:
    instances: 2
    memory: "4g"
```

## 2. Spark Operator Architecture

The Spark Operator follows the standard Kubernetes Operator pattern:

1.  **CRD Controller**: Watches for events (Create, Update, Delete) on `SparkApplication` resources across configured namespaces.
2.  **Submission Runner**: When a `SparkApplication` is created, the operator generates the `spark-submit` command and executes it inside a simplified "submission" pod or internally.
3.  **Spark Pod Monitor**: Watches the status of the Driver and Executor pods and updates the `.status` field of the `SparkApplication` resource.
4.  **Mutating Admission Webhook**: An optional but recommended component that intercepts pod creation requests. It injects Spark-specific configuration (like mounting ConfigMaps or Volumes) into the Driver and Executor pods before they are scheduled.

### Flow on OpenShift

1.  User applies `SparkApplication` YAML.
2.  Operator Controller (running in `kubeflow-spark-operator` namespace) detects the new resource.
3.  Operator creates a **Driver Pod** in the target namespace (e.g., `docling-spark`).
4.  Driver Pod starts and requests **Executor Pods** from the Kubernetes API server.
5.  Executor Pods start, connect to the Driver, and process the tasks.

![Spark Operator Flow on OpenShift](diagrams/Screenshot%202025-11-19%20at%209.35.21%E2%80%AFPM.png)

## 3. Installation on OpenShift

Installing the Spark Operator on OpenShift requires Helm and applying specific security patches to work with OpenShift's default security context constraints (SCC).

### Prerequisites
*   OpenShift CLI (`oc`)
*   Helm CLI (`helm`)
*   Cluster Admin privileges

### Installation Steps

1.  **Add the Helm Repository**:
    ```bash
    helm repo add spark-operator https://kubeflow.github.io/spark-operator
    helm repo update
    ```

2.  **Install the Operator**:
    Run the following command to install the operator in the `spark-operator` namespace.

    ```bash
    helm install spark-operator spark-operator/spark-operator \
        --namespace spark-operator \
        --create-namespace \
        --version 1.1.27 \
        --set webhook.enable=true \
        --set spark.jobNamespaces='{}'  # Watch all namespaces
    ```

3.  **Apply OpenShift Security Patches**:
    OpenShift is stricter than standard Kubernetes about running containers as root or with specific security contexts. You must remove incompatible security contexts from the operator's deployment.

    ```bash
    # Patch the Controller
    kubectl patch deployment spark-operator-controller -n spark-operator --type='json' \
      -p='[{"op": "remove", "path": "/spec/template/spec/securityContext/fsGroup"}]'

    kubectl patch deployment spark-operator-controller -n spark-operator --type='json' \
      -p='[{"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/seccompProfile"}]'

    # Patch the Webhook
    kubectl patch deployment spark-operator-webhook -n spark-operator --type='json' \
      -p='[{"op": "remove", "path": "/spec/template/spec/securityContext/fsGroup"}]'

    kubectl patch deployment spark-operator-webhook -n spark-operator --type='json' \
      -p='[{"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/seccompProfile"}]'
    ```

## 4. Debugging and Logging

### Operator Logs
If your Spark jobs are not starting (e.g., no pods created), check the operator logs:

```bash
oc logs -n spark-operator -l app.kubernetes.io/name=spark-operator
```

### Application Logs
Once the Driver pod is created, check its logs for Spark-specific initialization and application output:

```bash
# Check Driver logs
oc logs docling-spark-job-driver -n docling-spark

# Check Executor logs
oc logs docling-spark-job-exec-1 -n docling-spark
```

### SparkApplication Status
Inspect the status of the CRD to see if the operator encountered validation errors or submission failures:

```bash
oc describe sparkapplication docling-spark-job -n docling-spark
```

## 5. Running the Example Workload (Docling + Spark)

This repository contains a complete example of a distributed Spark job that uses the `docling` library to process PDFs.

### Component Overview
*   **`scripts/run_spark_job.py`**: The PySpark driver script. It defines a UDF (User Defined Function) that wraps the `docling` processor.
*   **`Dockerfile`**: Builds a custom Spark image containing `docling`, `tesseract`, and other dependencies.
*   **`k8s/docling-spark-app.yaml`**: The `SparkApplication` definition.

![Spark Workload Flow](diagrams/Mermaid%20Chart%20-%20Create%20complex%2C%20visual%20diagrams%20with%20text.-2025-11-20-023412.png)

### Running the Job

1.  **Clone the Repository** and navigate to the root.

2.  **Deploy using the Script**:
    The included `deploy.sh` script handles namespace creation, RBAC setup, SCC configuration (crucial for OpenShift), and job submission.

    ```bash
    ./k8s/deploy.sh
    ```

    **What this script does:**
    *   Creates/Ensures namespace `docling-spark`.
    *   Creates ServiceAccount `spark-driver` and binds necessary roles.
    *   **OpenShift Specific**: Adds the `anyuid` SCC to `spark-driver` so the Spark image (UID 185) can run.
    *   Applies `k8s/docling-spark-app.yaml`.

3.  **Verify Execution**:
    
    Watch the pods start up:
    ```bash
    oc get pods -n docling-spark -w
    ```
    
    You should see:
    *   `docling-spark-job-driver` (Running)
    *   `docling-spark-job-exec-1` (Running)
    *   `docling-spark-job-exec-2` (Running)

4.  **Check Results**:
    The example job processes PDFs in `/app/assets` and saves results to `/app/output/results.jsonl`.
    
    Since this example keeps the driver running for 1 hour after completion (to allow file copy), you can download the results:

    ```bash
    oc cp docling-spark-job-driver:/app/output/results.jsonl ./output/results.jsonl -n docling-spark
    ```

### References
*   [Red Hat Developer: Raw Data to Model Serving](https://developers.redhat.com/articles/2025/07/29/raw-data-model-serving-openshift-ai)
*   [Red Hat Access: Spark Operator on OpenShift](https://access.redhat.com/articles/7131048)
*   [Kubeflow Spark Operator GitHub](https://github.com/kubeflow/spark-operator)

