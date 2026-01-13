# Order Management API

A FastAPI REST API for querying order management database. The API exposes database query functions as GET endpoints with automatic Swagger documentation.

## Features

- REST API endpoints for querying customers, orders, transactions, and refunds
- Automatic database initialization from JSON files on startup
- Self-contained Docker image with all data files included
- Swagger/OpenAPI documentation at `/docs`
- Built with FastAPI and SQLite

## API Endpoints

### Customer
- `GET /api/customer?email=...` - Find customer by email
- `GET /api/customer?customer_id=...` - Find customer by customer ID
- `GET /api/customer?email=...&customer_id=...` - Find customer by email or customer ID

### Order
- `GET /api/order?order_no=...` - Find order by order number

### Transaction
- `GET /api/transaction?transaction_id=...` - Find transaction by transaction ID
- `GET /api/transaction/order/{order_no}` - Get transaction for an order

### Refund
- `GET /api/refund/order/{order_no}` - Get refund for an order

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Docker Deployment

The Docker image is self-contained and includes all JSON data files. The database is automatically initialized from these files when the container starts.

### Building the Docker Image

```bash
docker build -t order-management-api .
```

### Running the Container

```bash
docker run -d -p 8000:8000 --name order-management-api order-management-api
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Stopping the Container

```bash
docker stop order-management-api
docker rm order-management-api
```

## AWS ECR Deployment

To deploy the Docker image to AWS Elastic Container Registry (ECR) for use with AWS services like App Runner, ECS, or Lambda:

### Prerequisites

- AWS CLI installed and configured
- Docker installed
- AWS account with permissions to create/push to ECR repositories

### Step 1: Create ECR Repository

```bash
# Replace REGION and ACCOUNT_ID with your AWS region and account ID
aws ecr create-repository \
    --repository-name order-management-api \
    --region us-east-1
```

Or create it via AWS Console: ECR → Repositories → Create repository

### Step 2: Authenticate Docker with ECR

```bash
# Replace REGION and ACCOUNT_ID with your values
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### Step 3: Tag the Docker Image

```bash
# Replace ACCOUNT_ID and REGION with your values
docker tag order-management-api:latest \
    ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/order-management-api:latest
```

### Step 4: Push the Image to ECR

```bash
# Replace ACCOUNT_ID and REGION with your values
docker push \
    ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/order-management-api:latest
```

### Complete Example Script

```bash
#!/bin/bash
# Set your AWS region and account ID
REGION="us-east-1"
ACCOUNT_ID="123456789012"
REPO_NAME="order-management-api"

# Build the image
docker build -t $REPO_NAME .

# Authenticate Docker with ECR
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag the image
docker tag $REPO_NAME:latest \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Push the image
docker push \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

echo "Image pushed successfully!"
echo "Image URI: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest"
```

**Note:** After pushing, you can use this ECR image URI in AWS App Runner, ECS, EKS, or other container services.

## EKS Cluster Deployment

Deploy the Order Management API to Amazon EKS using AutoMode. EKS AutoMode automatically manages EC2 instances, compute autoscaling, pod networking, load balancing, storage, and cluster DNS.

### Prerequisites

1. **AWS CLI** installed and configured
2. **eksctl** version 0.221.0 or greater ([Installation Guide](https://eksctl.io/introduction/installation/))
3. **kubectl** installed
4. **Docker** installed
5. AWS account with permissions to create EKS clusters, ECR repositories, and manage EC2/VPC resources

### Step 1: Build and Push Docker Image to ECR

First, build and push your Docker image to ECR (see [AWS ECR Deployment](#aws-ecr-deployment) section above for detailed steps):

```bash
# Set your AWS region and account ID
export REGION="us-east-1"
export ACCOUNT_ID="123456789012"
export REPO_NAME="order-management-api"

# Build the image
docker build -t $REPO_NAME .

# Create ECR repository (if not already created)
aws ecr create-repository \
    --repository-name $REPO_NAME \
    --region $REGION

# Authenticate Docker with ECR
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag the image
docker tag $REPO_NAME:latest \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Push the image
docker push \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
```

### Step 2: Update Configuration Files

**⚠️ IMPORTANT: Before deploying, you must replace the placeholders in the manifest files with your actual AWS account details.**

Update the manifests with your AWS account details:

```bash
cd manifest

# Set your AWS account ID and region
export ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"  # e.g., "829040135710"
export REGION="us-west-2"  # or your preferred region

# Update cluster.yaml with your preferred region (if different from us-west-2)
# Edit cluster.yaml and change the region if needed

# Update deployment.yaml with your ECR image URI
sed -i "s/ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/g" deployment.yaml
```

**Or manually edit `manifest/deployment.yaml`** and replace the placeholders in the image field:
- Replace `ACCOUNT_ID` with your AWS account ID (12-digit number)
- Replace `REGION` with your AWS region (e.g., `us-west-2`, `us-east-1`)

Example: Change `ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/order-management-api:latest` to `829040135710.dkr.ecr.us-west-2.amazonaws.com/order-management-api:latest`

**Manifest Files:**
- `cluster.yaml` - eksctl configuration for creating EKS AutoMode cluster
- `deployment.yaml` - Kubernetes Deployment for the application
- `service.yaml` - Kubernetes Service (ClusterIP)
- `ingressclassparams.yaml` - IngressClassParams for ALB configuration
- `ingressclass.yaml` - IngressClass using EKS AutoMode controller
- `ingress.yaml` - Ingress resource for public ALB endpoint

### Step 3: Create EKS AutoMode Cluster

```bash
# Ensure you have the correct eksctl version
eksctl version  # Should be 0.221.0 or greater

# Create the EKS AutoMode cluster
eksctl create cluster -f cluster.yaml

# This will take 15-20 minutes. Wait for cluster to be ready.
# AutoMode will automatically create default node pools (general-purpose and system)
```

The cluster creation process will:
- Create the EKS control plane
- Set up VPC and networking
- Configure IAM roles
- Enable AutoMode with automatic node provisioning
- Configure kubectl automatically

### Step 4: Verify Cluster Access

```bash
# Verify kubectl is configured (eksctl does this automatically)
kubectl get nodes

# Verify cluster status
aws eks describe-cluster --name order-management-cluster --region us-west-2
```

### Step 5: Deploy the Application

```bash
# Navigate to manifest directory
cd manifest

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

### Step 6: Get the Public Endpoint

Wait for the Application Load Balancer to be created (may take 2-3 minutes):

```bash
# Check ingress status
kubectl get ingress order-management-api-ingress

# Get the ALB hostname
kubectl get ingress order-management-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Example output: k8s-default-order-xxxxx.us-east-1.elb.amazonaws.com
```

### Step 7: Access the API

Once the Ingress is ready, access your API at:
- **API**: `http://<ALB-ADDRESS>`
- **Swagger UI**: `http://<ALB-ADDRESS>/docs`
- **ReDoc**: `http://<ALB-ADDRESS>/redoc`

### Monitoring and Troubleshooting

```bash
# View pod logs
kubectl logs -f deployment/order-management-api

# View pod status
kubectl get pods -l app=order-management-api

# Describe resources for troubleshooting
kubectl describe deployment order-management-api
kubectl describe ingress order-management-api-ingress
kubectl describe pod <pod-name>

# Check cluster events
kubectl get events --sort-by='.lastTimestamp'
```

### Scaling

```bash
# Scale the deployment
kubectl scale deployment order-management-api --replicas=3

# Or edit the deployment
kubectl edit deployment order-management-api
```

EKS AutoMode will automatically provision additional EC2 instances as needed to accommodate the scaled pods.

### Optional: Enable HTTPS

1. Request or import an SSL certificate in AWS Certificate Manager (ACM)
2. Update `manifest/ingressclassparams.yaml` and uncomment the `certificateARNs` section
3. Replace `REGION`, `ACCOUNT_ID`, and `CERT_ID` with your values
4. Apply the updated IngressClassParams:
   ```bash
   kubectl apply -f manifest/ingressclassparams.yaml
   ```
5. The ALB will automatically use the certificate for HTTPS traffic

### Cleanup

To delete all resources:

```bash
# Delete application resources
kubectl delete -f manifest/ingress.yaml
kubectl delete -f manifest/ingressclass.yaml
kubectl delete -f manifest/ingressclassparams.yaml
kubectl delete -f manifest/service.yaml
kubectl delete -f manifest/deployment.yaml

# EKS AutoMode will automatically delete the associated ALB

# Delete the cluster (this will delete everything including nodes and networking)
eksctl delete cluster -f manifest/cluster.yaml
```

### Important Notes

- **EKS AutoMode**: Automatically manages EC2 instances, compute autoscaling, pod networking, load balancing, storage, and cluster DNS
- **Built-in Load Balancer**: No need to install AWS Load Balancer Controller - AutoMode includes built-in load balancer management
- **Cost**: You pay for EC2 instances used plus a management fee for AutoMode-managed nodes
- **Database**: The SQLite database is ephemeral - data resets on pod restart. For production, consider using RDS or DynamoDB
- **Region**: Update the region in `manifest/cluster.yaml` to match your preferred AWS region

For more detailed information, see the [manifest/README.md](manifest/README.md) file.

## Local Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
uv pip install -e .

# Run the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## Project Structure

```
order-management-api/
├── pyproject.toml          # Project configuration
├── Dockerfile              # Docker configuration
├── .dockerignore           # Docker ignore file
├── README.md               # This file
├── data/                   # JSON data files (copied into Docker)
│   ├── customers.json
│   ├── orders.json
│   ├── transactions.json
│   └── refunds.json
└── src/
    ├── config.py           # Configuration class
    ├── api/
    │   └── main.py         # FastAPI application
    └── services/
        └── database.py     # DatabaseService
```

## Database

The application uses SQLite and automatically initializes the database from JSON files in the `data/` directory on startup. The database file is created at `./data/temp/order-management.db` inside the container.

## Notes

- The Docker image is self-contained - no volume mounting required
- All JSON data files are copied into the image during build
- The database file is created inside the container on startup
- The API is read-only - no data modification operations are supported
