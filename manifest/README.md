# EKS Deployment Manifests

This directory contains Kubernetes manifests for deploying the Order Management API to Amazon EKS using AutoMode. EKS AutoMode automatically manages EC2 instances, compute autoscaling, pod networking, load balancing, storage, and cluster DNS.

## Prerequisites

1. **AWS CLI** installed and configured
2. **eksctl** installed ([Installation Guide](https://eksctl.io/introduction/installation/))
3. **kubectl** installed
4. **Docker image** pushed to ECR (see main README.md for ECR push instructions)

**Note:** EKS AutoMode includes built-in load balancer management, so you do NOT need to install the AWS Load Balancer Controller separately.

## Files

- `cluster.yaml` - eksctl configuration for creating EKS AutoMode cluster
- `deployment.yaml` - Kubernetes Deployment for the application
- `service.yaml` - Kubernetes Service (ClusterIP)
- `ingressclassparams.yaml` - IngressClassParams for ALB configuration
- `ingressclass.yaml` - IngressClass using EKS AutoMode controller
- `ingress.yaml` - Ingress resource for public ALB endpoint

## Step-by-Step Deployment

### 1. Create EKS AutoMode Cluster

```bash
# Ensure you have eksctl version 0.195.0 or greater
eksctl version

# Update cluster.yaml with your preferred region
# Then create the cluster with AutoMode enabled
eksctl create cluster -f cluster.yaml

# This will take 15-20 minutes. Wait for cluster to be ready.
# AutoMode will automatically create default node pools (general-purpose and system)
```

### 2. Configure kubectl

```bash
# eksctl automatically configures kubectl, but you can verify:
aws eks update-kubeconfig --name order-management-cluster --region us-east-1
```

### 3. Update Deployment with ECR Image

Before deploying, update the image in `deployment.yaml`:

```bash
# Replace ACCOUNT_ID and REGION with your values
sed -i 's/ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/g' deployment.yaml
```

Or manually edit `deployment.yaml` and replace:
- `ACCOUNT_ID` with your AWS account ID
- `REGION` with your AWS region (e.g., `us-east-1`)

### 4. Deploy the Application

```bash
# Apply all manifests in order
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingressclassparams.yaml
kubectl apply -f ingressclass.yaml
kubectl apply -f ingress.yaml

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get services
kubectl get ingressclass
kubectl get ingressclassparams
kubectl get ingress
```

### 5. Get the Public Endpoint

```bash
# Wait for the ALB to be created (may take 2-3 minutes)
kubectl get ingress order-management-api-ingress

# Get the ALB hostname
kubectl get ingress order-management-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Example output: k8s-default-order-xxxxx.us-east-1.elb.amazonaws.com
```

### 6. Access the API

Once the Ingress is ready, access your API at:
- API: `http://<ALB-ADDRESS>`
- Swagger UI: `http://<ALB-ADDRESS>/docs`
- ReDoc: `http://<ALB-ADDRESS>/redoc`

## Optional: HTTPS Configuration

To enable HTTPS:

1. Request or import an SSL certificate in AWS Certificate Manager (ACM)
2. Update `ingressclassparams.yaml` and uncomment the `certificateARNs` section
3. Replace `REGION`, `ACCOUNT_ID`, and `CERT_ID` with your values
4. Apply the updated IngressClassParams:
   ```bash
   kubectl apply -f ingressclassparams.yaml
   ```
5. The ALB will automatically use the certificate for HTTPS traffic

## Scaling

To scale the deployment:

```bash
# Scale to 3 replicas
kubectl scale deployment order-management-api --replicas=3

# Or edit the deployment
kubectl edit deployment order-management-api
```

## Monitoring

```bash
# View pod logs
kubectl logs -f deployment/order-management-api

# View pod status
kubectl get pods -l app=order-management-api

# Describe resources for troubleshooting
kubectl describe deployment order-management-api
kubectl describe ingress order-management-api-ingress
```

## Cleanup

To delete all resources:

```bash
# Delete application resources
kubectl delete -f ingress.yaml
kubectl delete -f ingressclass.yaml
kubectl delete -f ingressclassparams.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml

# EKS AutoMode will automatically delete the associated ALB

# Delete the cluster (this will delete everything)
eksctl delete cluster -f cluster.yaml
```

## Notes

- **EKS AutoMode**: The cluster uses EKS AutoMode, which automatically manages EC2 instances using a Karpenter-based system. AutoMode handles compute autoscaling, pod networking, load balancing, storage, and cluster DNS automatically.
- **Built-in Load Balancer**: EKS AutoMode includes built-in load balancer management - you do NOT need to install the AWS Load Balancer Controller separately. Use IngressClass with `controller: eks.amazonaws.com/alb` instead.
- **Compute**: AutoMode automatically provisions EC2 instances in response to pod requests. You pay for the EC2 instances used, plus a management fee for AutoMode-managed nodes.
- **Node Pools**: AutoMode creates default node pools (`general-purpose` and `system`) automatically. You can create additional node pools via the Kubernetes API if needed.
- **Database**: The SQLite database is ephemeral - data resets on pod restart. For production, consider using RDS or DynamoDB
- **Region**: Update the region in `cluster.yaml` to match your preferred AWS region
- **eksctl Version**: Requires eksctl version 0.195.0 or greater
