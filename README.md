# Agumbe
A Kubernetes replication controller to clone objects. [Blog](https://medium.com/@savvythrough/agumbe-a-kubernetes-operator-to-create-globalsecrets-f73c19103141?source=friends_link&sk=ea432e64dba40cecbe17618e58e4c656) post explains the concept & the problem it's trying to solve.

### Install
To install in your cluster
```
  $ kubectl create namespace agumbe

  $ helm install agumbe helm --namespace agumbe
```

### Example
1. Create target namespaces to which the object has to be replicated
```
  $ for namespace in red blue green; do kubectl create ns $namespace; done
```
2. Create a few namespaces with labels on them
```
  $ for namespace in yellow orange; do kubectl create ns $namespace && kubectl label ns $namespace infra.savilabs.io/owner=admin; done
```
2. Create the source object that needs to be replicated
```
  $ kubectl create -f examples/configmap.yaml

  NOTE: Agumbe currently supports objects of type ["Secrets", "ConfigMaps"]
```
3. Modify the global object. This step will contain the config needed to replicate the object created in STEP2
```
  ---
  apiVersion: savilabs.io/v1alpha1
  kind: GlobalObject
  metadata:
    name: <Required: NAME-OF-THE-GLOBAL-OBJECT>
    namespace: <Required: NAMESPACE>
  spec:
    type: <Required: CAN-BE-ONE-OFF-["Secret", "ConfigMap"]>
    name: <Required: NAME-OF-SOURCE-OBJECT-CREATED-IN-STEP2>
    targetName: <Optional: NAME-OF-THE-REPLICATED-OBJECT>
    targetNamespaces: <Optional: <LIST-OF-TARGET-NAMESPACES>
    matchLabels:
    - key: <Optional: NAMESPACE-LABEL-KEY>
      value: <Optional: NAMESPACE-LABEL-VALUE>
```
4. Create the global object
```
  $ kubectl apply -f examples/globalObject.yaml
```
5. Verify that the object is replicated in target namespaces
```
  $ kubectl get configmap cm-april-2020 -o json -n $namespace | jq -r ".data"

  $ for namespace in red blue green yellow orange; do kubectl get configmap my-configmap -o json -n $namespace | jq -r ".data"; done
```
6. Replace `spec.name` in **STEP3** to point to the second configMap `cm-may-2020` & rerun **STEP4**
```
  $ kubectl apply -f examples/globalObject.yaml
```
7. Observe that the value of the configMap in the target namespaces have been modified
```
  $ kubectl get configmap cm-may-2020 -o json -n $namespace | jq -r ".data"
  
  $ for namespace in red blue green yellow orange; do kubectl get configmap my-configmap -o json -n $namespace | jq -r ".data"; done
```
8. Observe replication logs on the controller
```
  $ kubectl logs deploy/agumbe -n agumbe -f
```
