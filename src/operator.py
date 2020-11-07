#!/usr/bin/env python

from itertools import chain
from time import time

import kopf
import yaml
from kubernetes import client, config
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

        self.apiMap = kwargs['apiMap']

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
            self.listNamespaces = [item.metadata.name for item in
                                   self.apiMap['namespace']['client'].list_namespace().items]
        except ApiException as e:
            self.logger.error(f'{self.event.upper()}: {e}')

    def __replicate(self):
        """
        Function to CRU objects
        """

        sourceObj = self.readObj(name=self.srcObjName, namespace=self.srcNamespace,
                                 export=True)
        jsonObj = self.apiMap['sanitize']['client'].sanitize_for_serialization(sourceObj)
        jsonObj['metadata']['name'] = self.destObjName

        for destNamespace in self.destNamespaces:
            try:
                objList = [item.metadata.name for item in
                           self.listObj(namespace=destNamespace).items]
                objInList = True if self.destObjName in objList else False

                if self.event in ['create', 'update']:
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
                    labelFilter = f'{label["key"]}={label["value"]}'
                    matchNamespaces = [item.metadata.name for item in
                                       self.apiMap['namespace']['client'].list_namespace(
                                           label_selector=labelFilter).items]
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

            lowerSrcObjType = self.srcObjType.lower()

            if lowerSrcObjType in self.apiMap:
                self.readObj = getattr(self.apiMap[lowerSrcObjType]['client'],
                                       f'read_namespaced_{self.apiMap[lowerSrcObjType]["convention"]}')
                self.listObj = getattr(self.apiMap[lowerSrcObjType]['client'],
                                       f'list_namespaced_{self.apiMap[lowerSrcObjType]["convention"]}')
                self.createObj = getattr(self.apiMap[lowerSrcObjType]['client'],
                                         f'create_namespaced_{self.apiMap[lowerSrcObjType]["convention"]}')
                self.replaceObj = getattr(self.apiMap[lowerSrcObjType]['client'],
                                          f'replace_namespaced_{self.apiMap[lowerSrcObjType]["convention"]}')
                self.__replicate()
            else:
                self.logger.error(f'{self.event.upper()}: Object type "{self.srcObjType}" not supported')

        except ApiException as e:
            self.logger.error(f'{self.event.upper()}: {e}')


@kopf.on.create('savilabs.io', 'v1alpha1', 'globalobjects')
@kopf.on.update('savilabs.io', 'v1alpha1', 'globalobjects')
def globalObject(event, spec, name, namespace, logger, **kwargs):
    """
        Create object on event
    """

    try:
        apiMap = globalMap
        go = Agumbe(**locals())
        start = time()
        go.processObject()
        end = time()
        logger.info(f'{event.upper()}: Execution time: {end - start} seconds')
    except Exception as e:
        logger.error(
            f'{event.upper()}: {e}')


def main():
    """
        Load config from file
    """

    config.load_incluster_config()

    global globalMap
    globalMap = dict()

    with open("conf/resources.yaml", 'r') as stream:
        try:
            conf = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)

    for item in chain(conf['core'], conf['scoped']):
        apiObj = getattr(client, item['api'])()
        objConvention = item['convention'] if item.get('convention') else item['name']
        globalMap[item['name']] = {'client': apiObj, 'convention': objConvention}


main()
