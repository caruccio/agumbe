import kopf
from kubernetes import client

class Agumbe(object):
    """
    API to duplicate objects
    """

    def __init__(self, event, body, spec, name, namespace, logger, **kwargs):
        self.apiCore = client.CoreV1Api()
        self.apiApi = client.ApiClient()

        self.event = event
        self.logger = logger

        self.globalObjectName = name

        self.srcNamespace = namespace
        self.srcObjType = spec['type']
        self.srcObjName = spec['name']

        self.destObjName = spec['targetName'] if spec.get('targetName') else spec['name']
        self.destNamespaces = spec['targetNamespaces']

    def secret(self):

        """
        Function to CRU Secrets
        """

        readSourceObj = self.apiCore.read_namespaced_secret(name=self.srcObjName, namespace=self.srcNamespace,
                                                            export=True)
        jsonSourceObj = self.apiApi.sanitize_for_serialization(readSourceObj)

        try:
            for namespace in self.destNamespaces:
                objList = self.apiCore.list_namespaced_config_map(namespace=namespace)
                objInList = True if self.destObjName in objList else False

                if self.event == "create":
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_secret(name=self.destObjName,
                                                                         namespace=namespace, body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_secret(namespace=namespace, body=jsonSourceObj)

                elif self.event == "update":
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_secret(name=self.destObjName,
                                                                         namespace=namespace, body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_secret(namespace=namespace, body=jsonSourceObj)

                self.logger.info(
                    f'{self.event.upper()}: Secret {self.srcNamespace}/{self.srcObjType}/{self.srcObjName} duped to '
                    f'{self.destNamespace}/{self.srcObjType}/{destObj.metadata.name}')

        except Exception as e:
            self.logger.error(
                f'{self.event.upper()}: Secret {self.srcNamespace}/{self.srcObjType}/{self.srcObjName} failed to dupe '
                f'into {self.destNamespace}')

    def configMap(self):

        """
        Function to CRU ConfigMaps
        """

        readSourceObj = self.apiCore.read_namespaced_config_map(name=self.srcObjName, namespace=self.srcNamespace,
                                                                export=True)
        jsonSourceObj = self.apiApi.sanitize_for_serialization(readSourceObj)

        try:
            for namespace in self.destNamespaces:
                objList = self.apiCore.list_namespaced_config_map(namespace=namespace)
                objInList = True if self.destObjName in objList else False

                if self.event == "create":
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_config_map(name=self.destObjName,
                                                                             namespace=namespace, body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_config_map(namespace=namespace, body=jsonSourceObj)

                elif self.event == "update":
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_config_map(name=self.destObjName,
                                                                             namespace=namespace, body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_config_map(namespace=namespace, body=jsonSourceObj)

                self.logger.info(
                    f'{self.event.upper()}: Secret {self.srcNamespace}/{self.srcObjType}/{self.srcObjName} duped to '
                    f'{self.destNamespace}/{self.srcObjType}/{destObj.metadata.name}')

        except Exception as e:
            self.logger.error(
                f'{self.event.upper()}: Secret {self.srcNamespace}/{self.srcObjType}/{self.srcObjName} failed to dupe '
                f'into {self.destNamespace}')

    def processObject(self):

        try:
            self.logger.info(
                f'{self.event.upper()}: GlobalObject "{self.srcNamespace}/GlobalObject/{self.srcObjType}/{self.globalObjectName}" '
                f'created')

            if srcObjType.lower() == "secret":
                response = secret()

            elif srcObjType.lower() == "configmap":
                response = configMap()

        except Exception as e:
            raise self.logger.error(
                f'{self.event.upper()}: Failed to fetch "{self.srcNamespace}/GlobalObject/{self.srcObjType}/{self.globalObjectName}"')
            
@kopf.on.resume('einstein.ai', 'v1alpha1', 'globalobjects')
@kopf.on.create('einstein.ai', 'v1alpha1', 'globalobjects')
@kopf.on.update('einstein.ai', 'v1alpha1', 'globalobjects')
    def test(event, body, spec, name, namespace, logger, **kwargs):
        x = Agumbe(event, body, spec, name, namespace, logger)
        x.processObject()
