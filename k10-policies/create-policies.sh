#!/bin/bash

# Nhập giá trị cho presetRef.name
read -p "Enter the prefix for presetRef.name (e.g., weekly): " presetName

# Lấy thông tin ứng dụng và namespace
apps=$(kubectl get applications.argoproj.io -A -o json | jq -r '.items[] | "\(.metadata.name) \(.spec.destination.namespace)"')

# Xử lý từng dòng trong đầu ra
while IFS=' ' read -r app_name app_namespace; do
  # Tạo file YAML cho mỗi ứng dụng
  cat <<EOF >"${app_name}-backup-policy.yaml"
kind: Policy
apiVersion: config.kio.kasten.io/v1alpha1
metadata:
  name: ${app_name}-weekly
  namespace: k10
spec:
  presetRef:
    name: $presetName
    namespace: k10
  selector:
    matchExpressions:
      - key: k10.kasten.io/appNamespace
        operator: In
        values:
          - ${app_namespace}
  actions:
    - action: backup
      backupParameters:
        filters:
          includeResources:
            - matchExpressions:
                - key: argocd.argoproj.io/instance
                  operator: In
                  values:
                    - ${app_name}
  createdBy: admin@example.com
status:
  validation: Success
EOF

  echo "Created policy file for: ${app_name} in namespace: ${app_namespace}"
done <<< "$apps"

echo "All policy files have been created."
