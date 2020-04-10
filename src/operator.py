import kopf
from kubernetes import client

def validate(spec):

  if not spec.get('secretName'):
    raise kopf.PermanentError(f"Secret Name is a required value (type: String)")

  if not spec.get('targetNamespaces'):
    raise kopf.PermanentError(f"Target Namespace is a required value (type: List)")

  secret = spec['secretName']
  targetNamespaces = spec['targetNamespaces']

  if spec.get('targetSecretName'):
    targetSecretName = spec['targetSecretName']
  else:
    targetSecretName = spec['secretName']

  return secret, targetNamespaces, targetSecretName


def getSecret(apiCore, apiApi, namespace, spec):

  try:
    secret, targetNamespaces, targetSecretName = validate(spec)
    getObj = apiCore.read_namespaced_secret(name=secret, namespace=namespace, export=True)

    jsonObj = apiApi.sanitize_for_serialization(getObj)
    jsonObj['metadata']['name'] = targetSecretName

    return jsonObj, targetNamespaces, targetSecretName

  except Exception as e:
    raise kopf.HandlerFatalError(f'Failed to fetch secret {secret}')


@kopf.on.create('savilabs.io', 'v1alpha1', 'globalsecrets')
@kopf.on.update('savilabs.io', 'v1alpha1', 'globalsecrets')
def createUpdate(event, body, spec, name, namespace, logger, **kwargs):

  oper = event
  secretName = spec['secretName']
  annotation = 'savilabs.io/v1alpha1/GlobalSecret/{0}'.format(namespace)
  logger.info(f'{annotation}/{name} created')

  apiCore = client.CoreV1Api()
  apiApi = client.ApiClient()
  getObj, targetNamespaces, targetSecretName = getSecret(apiCore, apiApi, namespace, spec)

  for targetNamespace in targetNamespaces:

    try:
      if oper == "create":
        createObj = apiCore.create_namespaced_secret(namespace=targetNamespace, body=getObj)

      elif oper == "update":
        try:
          createObj = apiCore.replace_namespaced_secret(name=targetSecretName, namespace=targetNamespace, body=getObj)
        except Exception as e:
          createObj = apiCore.create_namespaced_secret(namespace=targetNamespace, body=getObj)

      logger.info(f'{oper.upper()}: Secret {namespace}/{secretName} duped to {targetNamespace}/{createObj.metadata.name}')

    except Exception as e:
        logger.error(f'{oper.upper()}: Secret {namespace}/{secretName} failed to dupe into {targetNamespace}')
