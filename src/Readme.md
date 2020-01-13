## AGUMBE

1) Global Secrets Replicator

   - Create role
     `kubectl create -f role.yaml`

   - Create custom resource definition
     `kubectl create -f crd.yaml`

   - Create global secret
     `kubectl create -f global-secret.yaml`

   - Verify
     `kubectl get gs` 
