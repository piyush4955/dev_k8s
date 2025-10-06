#!/bin/bash

# Chaos script: randomly kills one pod every 30s

#!/bin/bash
# Randomly delete one fastapi-app pod in namespace microservice
POD=$(kubectl get pods -n microservice -l app=fastapi-app -o jsonpath='{.items[0].metadata.name}')
echo "Deleting pod: $POD"
kubectl delete pod $POD -n microservice
