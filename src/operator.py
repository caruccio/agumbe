#!/usr/bin/env python

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

class Agumbe(object):
    
    """
    API to duplicate objects

    Attributes:
        event: Action on the GlobalObject (CRUD)
        spec: Specification of the GlobalObject
        name: Name of the GlobalObject
        namespace: Namespace in which the GlobalObject resides
        logger: Logger object
    """

    def __init__(self, **kwargs):

        self.apiCore = client.CoreV1Api()
        self.apiApi = client.ApiClient()

        self.event = kwargs['event']
        self.logger = kwargs['logger']

        self.globalObjectName = kwargs['name']
        self.srcNamespace = kwargs['namespace']
        self.srcObjType = kwargs['spec']['type']
        self.srcObjName = kwargs['spec']['name']
        self.destObjName = kwargs['spec']['targetName'] if kwargs['spec'].get('targetName') else kwargs['spec']['name']
        self.destNamespaces = list(dict.fromkeys(kwargs['spec']['targetNamespaces'])) if kwargs['spec'].get('targetNamespaces') else []
        self.namespaceLabels = kwargs['spec']['matchLabels'] if kwargs['spec'].get('matchLabels') else None

        try:
            self.listNamespaces = [item.metadata.name for item in self.apiCore.list_namespace().items]
        except ApiException as e:
            self.logger.error(f'{self.event.upper()}: {e}')

    def secret(self):

        """
        Function to CRU Secrets
        """

        readSourceObj = self.apiCore.read_namespaced_secret(name=self.srcObjName, namespace=self.srcNamespace,
                                                            export=True)
        jsonSourceObj = self.apiApi.sanitize_for_serialization(readSourceObj)
        jsonSourceObj['metadata']['name'] = self.destObjName

        for destNamespace in self.destNamespaces:
            try:
                objList = [item.metadata.name for item in
                           self.apiCore.list_namespaced_secret(namespace=destNamespace).items]
                objInList = True if self.destObjName in objList else False

                if self.event in ['create', 'update', 'resume']:
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_secret(name=self.destObjName,
                                                                         namespace=destNamespace, body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_secret(namespace=destNamespace, body=jsonSourceObj)

                    self.logger.info(
                        f'{self.event.upper()}: {self.srcObjType} "{self.srcNamespace}/{self.srcObjName}" duped to '
                        f'"{destNamespace}/{destObj.metadata.name}"')

            except ApiException as e:
                self.logger.error(f'{self.event.upper()}: {e}')
                self.logger.error(
                    f'{self.event.upper()}: {self.srcObjType} "{self.srcNamespace}/{self.srcObjName} failed to '
                    f'dupe '
                    f'into {destNamespace}')

    def configMap(self):

        """
        Function to CRU ConfigMaps
        """

        readSourceObj = self.apiCore.read_namespaced_config_map(name=self.srcObjName, namespace=self.srcNamespace,
                                                                export=True)
        jsonSourceObj = self.apiApi.sanitize_for_serialization(readSourceObj)
        jsonSourceObj['metadata']['name'] = self.destObjName

        for destNamespace in self.destNamespaces:
            try:
                objList = [item.metadata.name for item in
                           self.apiCore.list_namespaced_config_map(namespace=destNamespace).items]
                objInList = True if self.destObjName in objList else False

                if self.event in ['create', 'update', 'resume']:
                    if objInList:
                        destObj = self.apiCore.replace_namespaced_config_map(name=self.destObjName,
                                                                             namespace=destNamespace,
                                                                             body=jsonSourceObj)
                    else:
                        destObj = self.apiCore.create_namespaced_config_map(namespace=destNamespace, body=jsonSourceObj)

                    self.logger.info(
                        f'{self.event.upper()}: {self.srcObjType} "{self.srcNamespace}/{self.srcObjName}" duped to '
                        f'"{destNamespace}/{destObj.metadata.name}"')

            except ApiException as e:
                self.logger.error(f'{self.event.upper()}: {e}')
                self.logger.error(
                    f'{self.event.upper()}: {self.srcObjType} "{self.srcNamespace}/{self.srcObjName} failed to '
                    f'dupe '
                    f'into {destNamespace}')

    def processObject(self):

        """
        Function to Process Object
        """

        try:
            self.logger.info(
                f'{self.event.upper()}: GlobalObject "{self.srcNamespace}/{self.srcObjType}/'
                f'{self.globalObjectName}" '
                f'created')
            
            if self.namespaceLabels:
                for label in self.namespaceLabels:
                    labelFilter = '{}={}'.format(label['key'], label['value'])
                    matchNamespaces = [item.metadata.name for item in self.apiCore.list_namespace(label_selector=labelFilter).items]
                    if not matchNamespaces:
                        self.logger.error(
                            f'{self.event.upper()}: Failed to find namespaces with label "{labelFilter}"')
                        continue
                    else:
                        self.logger.info(
                            f'{self.event.upper()}: Namespaces {matchNamespaces} matched for label "{labelFilter}"')
                    self.destNamespaces += list(set(matchNamespaces))
            
            self.destNamespaces = list(dict.fromkeys(self.destNamespaces))
           
            diffList = [destNamespace for destNamespace in self.destNamespaces if
                        destNamespace not in self.listNamespaces]
            if diffList:
                self.logger.error(
                    f'{self.event.upper()}: Failed to find namespaces {diffList}')
                return

            if self.srcObjType.lower() == 'secret':
                response = self.secret()

            elif self.srcObjType.lower() == 'configmap':
                response = self.configMap()

            else:
                self.logger.error(f'{self.event.upper()}: Object type "{self.srcObjType}" not supported')

        except ApiException as e:
            self.logger.error(f'{self.event.upper()}: {e}')


@kopf.on.create('savilabs.io', 'v1alpha1', 'globalobjects')
@kopf.on.update('savilabs.io', 'v1alpha1', 'globalobjects')
def globalObject(event, spec, name, namespace, logger, **kwargs):
    try:
        go = Agumbe(**locals())
        go.processObject()
    except Exception as e:
        logger.error(
            f'{event.upper()}: {e}')
