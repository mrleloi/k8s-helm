#!/bin/bash

# Get all PVs that are currently set to Delete
PVs=$(kubectl get pv --no-headers | awk '$4=="Delete" {print $1}')

# Loop through the list of PVs and set their reclaim policy to Retain
for pv in $PVs; do
    kubectl patch pv $pv -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
    echo "Set Reclaim Policy to Retain for PV: $pv"
done
