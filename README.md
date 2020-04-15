# Agumbe
A Kubernetes replication controller to clone objects. [Blog](https://medium.com/@savvythrough/agumbe-a-kubernetes-operator-to-create-globalsecrets-f73c19103141?source=friends_link&sk=ea432e64dba40cecbe17618e58e4c656) post explains the concept & the problem it's trying to solve.

### Build
To build the docker image
```
  $ docker build . -t <tag>

  $ docker push
```

### Install
To install in your cluster
```
  $ kubectl create namespace agumbe

  $ helm install --name agumbe helm --namespace agumbe
```

### Example
```
  $ for namespace in {"red","blue", "green"}; do kubectl create ns $namespace; done
  
  $ kubectl create -f examples/configmap.yaml
  
  $ kubectl create -f examples/globalObject.yaml

  $ kubectl get configmaps --all-namespaces
```
