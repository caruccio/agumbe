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

        self.apiMap = {
            'secret': 'secret',
            'configmap': 'config_map',
            'deployment': 'deployment'
        }

        self.apiType = {
            'secret': client.CoreV1Api(),
            'configmap': client.CoreV1Api(),
            'deployment': client.AppsV1Api(),
            'namespace': client.CoreV1Api(),
            'sanitize': client.ApiClient()
        }

        self.event = kwargs['event']
        self.logger = kwargs['logger']

        self.globalObjectName = kwargs['name']
        self.srcNamespace = kwargs['namespace']
        self.srcObjType = kwargs['spec']['type']
        self.srcObjName = kwargs['spec']['name']
        self.destObjName = kwargs['spec']['targetName'] if kwargs['spec'].get('targetName') else kwargs['spec']['name']
        self.destNamespaces = list(dict.fromkeys(kwargs['spec']['targetNamespaces'])) if kwargs['spec'].get(
            'targetNamespaces') else []
        self.namespaceLabels = kwargs['spec']['matchLabels'] if kwargs['spec'].get('matchLabels') else None

        try:
            self.listNamespaces = [item.metadata.name for item in self.apiType['namespace'].list_namespace().items]
        except ApiException as e:
            self.logger.error(f'{self.event.upper()}: {e}')

    def replicate(self):

        """
        Function to CRU objects
        """

        readObj = self.readObj(name=self.srcObjName, namespace=self.srcNamespace,
                               export=True)
        jsonObj = self.apiType['sanitize'].sanitize_for_serialization(readObj)
        jsonObj['metadata']['name'] = self.destObjName

        for destNamespace in self.destNamespaces:
            try:
                objList = [item.metadata.name for item in
                           self.listObj(namespace=destNamespace).items]
                objInList = True if self.destObjName in objList else False

                if self.event in ['create', 'update', 'resume']:
                    if objInList:
                        destObj = self.replaceObj(name=self.destObjName,
                                                  namespace=destNamespace, body=jsonObj)
                    else:
                        destObj = self.createObj(namespace=destNamespace, body=jsonObj)

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
                    matchNamespaces = [item.metadata.name for item in
                                       self.apiType['namespace'].list_namespace(label_selector=labelFilter).items]
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

            if self.srcObjType.lower() in self.apiMap:
                self.readObj = getattr(self.apiType[self.srcObjType.lower()],
                                       f'read_namespaced_{self.apiMap[self.srcObjType.lower()]}')
                self.listObj = getattr(self.apiType[self.srcObjType.lower()],
                                       f'list_namespaced_{self.apiMap[self.srcObjType.lower()]}')
                self.createObj = getattr(self.apiType[self.srcObjType.lower()],
                                         f'create_namespaced_{self.apiMap[self.srcObjType.lower()]}')
                self.replaceObj = getattr(self.apiType[self.srcObjType.lower()],
                                          f'replace_namespaced_{self.apiMap[self.srcObjType.lower()]}')
                self.replicate()
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
        
