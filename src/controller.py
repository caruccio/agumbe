import os, sys
import requests
import json
import logging

log = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.INFO)
log.addHandler(out_hdlr)
log.setLevel(logging.INFO)

base_url = 'http://127.0.0.1:8001'

namespace = os.getenv('res_namespace', 'global-secrets')

def replicateSecrets(secret_name, target_namespace):

    remove_list = ['selfLink', 'uid', 'creationTimestamp', 'resourceVersion', 'annotations', 'namespace']

    url = '{0}/api/v1/namespaces/{1}/secrets/{2}'.format(base_url, 'global-secrets', secret_name)

    get_response = requests.get(url)
    data = get_response.json()

    if get_response.status_code == 200:
        pass
    else:
        log.error('{0}: Failed to get secret {1} in {2} namespace'.format(get_response.status_code, secret_name, namespace))

    for key in remove_list:

        try:
           data['metadata'].pop(key)
        except Exception as e:
            log.error('{0}'.format(e))

    for namespace in target_namespace[0]:

        url = '{0}/api/v1/namespaces/{1}/secrets/{2}'.format(base_url, namespace, secret_name)

        post_response = requests.post(url, data=data)
        print("xxx", url, data)

        if post_response.status_code == 200:
            log.info('Successfully replicated {0} to {1} namespace'.format(secret_name, namespace))
        else:
            log.error('{0}: Failed to replicate {1} to {2} namespace'.format(post_response.status_code, secret_name, namespace))


def getGlobalSecretConfig(secret_name):
    url = '{0}/apis/savilabs.io/v1alpha1/namespaces/{1}/globalsecrets'.format(base_url, namespace)
    response = requests.get(url).json()
    target_namespace = [secret['spec']['targetNamespace']
                       for secret in response['items'] if secret['spec']['secretName'] == secret_name]
    return target_namespace

def watchLoop():
    log.info('Starting agumbe controller')
    url = '{0}/api/v1/namespaces/{1}/secrets?watch=true'.format(base_url, namespace)
    response = requests.get(url, stream=True)
    for line in response.iter_lines():
        obj = json.loads(line.decode('utf8'))
        secret_name = obj['object']['metadata']['name']
        if 'annotations' in obj['object']['metadata'].keys():
            annotations = obj['object']['metadata']['annotations']
            print(secret_name,annotations)
        else:
            print(secret_name, "")
            continue
        if 'agumbe.savilabs.io' in annotations.keys():
            log.info('Secret {0} has matching annotation'.format(secret_name))
            target_namespace = getGlobalSecretConfig(secret_name)
            replicateSecrets(secret_name, target_namespace)
watchLoop()
