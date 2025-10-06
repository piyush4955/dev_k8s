#!/bin/bash
echo "Scaling down to 0 replicas..."
kubectl scale deployment fastapi-app -n microservice --replicas=0

echo "Waiting 60 seconds for alerts to fire..."
sleep 60

echo "Scaling back up to 2 replicas..."
kubectl scale deployment fastapi-app -n microservice --replicas=2

echo "Done! Pods should be recovering now."
