#!/bin/bash
echo "=== Final System Verification ==="

echo -e "\n1. Testing Slack Notifications..."
kubectl scale deployment fastapi-app -n microservice --replicas=0
echo "   Waiting 90 seconds for alert to fire..."
sleep 90
echo "   Check Slack #social channel - did you get a notification? (yes/no)"
read -p "   > " slack_response
kubectl scale deployment fastapi-app -n microservice --replicas=2

echo -e "\n2. Testing Prediction Script..."
python prediction/predict.py
echo "   Did it run without errors? (yes/no)"
read -p "   > " predict_response

echo -e "\n3. Testing Performance Analysis..."
./scripts/performance-analysis.sh
echo "   Did it show metrics? (yes/no)"
read -p "   > " perf_response

echo -e "\n4. Checking Prometheus Rules..."
kubectl get prometheusrule -n monitoring | grep fastapi
echo "   Do you see 3 rules (alert, recording, predictive)? (yes/no)"
read -p "   > " rules_response

echo -e "\n=== Summary ==="
[ "$slack_response" = "yes" ] && echo "✓ Slack notifications working" || echo "✗ Slack notifications FAILED"
[ "$predict_response" = "yes" ] && echo "✓ ML prediction working" || echo "✗ ML prediction FAILED"
[ "$perf_response" = "yes" ] && echo "✓ Performance analysis working" || echo "✗ Performance analysis FAILED"
[ "$rules_response" = "yes" ] && echo "✓ All rules configured" || echo "✗ Rules incomplete"

if [ "$slack_response" = "yes" ] && [ "$predict_response" = "yes" ] && [ "$perf_response" = "yes" ] && [ "$rules_response" = "yes" ]; then
    echo -e "\n🎉 PROJECT COMPLETE!"
else
    echo -e "\n⚠️ Some components need fixing"
fi
