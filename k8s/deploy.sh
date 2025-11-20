#!/bin/bash
# k8s/deploy.sh - Deploys Docling + PySpark (Supports ROSA/OpenShift & Standard K8s)
set -e

echo "Deploying Docling + PySpark"
echo "======================================"

NAMESPACE="docling-spark"
SERVICE_ACCOUNT="spark-driver"

# Step 1: Create Namespace
echo ""
echo "1.Ensuring namespace exists..."
# Use 'oc' if available (for ROSA), otherwise 'kubectl'
if command -v oc &> /dev/null; then
    if ! oc get project $NAMESPACE &> /dev/null; then
        oc new-project $NAMESPACE
    else
        oc project $NAMESPACE
    fi
else
    kubectl apply -f k8s/base/namespace.yaml
fi

# Step 2: Create RBAC
echo ""
echo "2. Creating RBAC (ServiceAccount, Role, RoleBinding)..."
kubectl apply -f k8s/base/rbac.yaml

# Step 3: ROSA/OpenShift Specific Configuration (SCC)
if command -v oc &> /dev/null; then
    echo ""
    echo "3. [ROSA/OpenShift Detected] Configuring SCC..."
    echo "   Allowing '$SERVICE_ACCOUNT' to run with any UID (needed for Spark images)..."
    oc adm policy add-scc-to-user anyuid -z $SERVICE_ACCOUNT -n $NAMESPACE
    echo "   ✅ SCC 'anyuid' added to ServiceAccount '$SERVICE_ACCOUNT'"
else
    echo ""
    echo "Standard Kubernetes detected (Skipping OpenShift SCC configuration)"
fi

# Step 4: Submit Spark Application
echo ""
echo "4. Submitting Spark Application..."
# Use replace --force to ensure the job is restarted if it already exists
kubectl replace --force -f k8s/docling-spark-app.yaml || kubectl create -f k8s/docling-spark-app.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status:"
echo "   kubectl get sparkapplications -n $NAMESPACE"
echo "   kubectl get pods -n $NAMESPACE -w"
echo ""
echo "📝 View logs:"
echo "   kubectl logs -f docling-spark-job-driver -n $NAMESPACE"
echo ""
echo "🌐 Access Spark UI (when driver is running):"
echo "   kubectl port-forward -n $NAMESPACE svc/docling-spark-job-ui-svc 4040:4040"
echo "   Open: http://localhost:4040"
echo ""
echo "💡 Note: PDFs are processed from /app/assets in the Docker image"
echo "   To process different PDFs, rebuild the image with new files in assets/"
