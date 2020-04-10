FROM python:3.7
ADD src/operator.py /src
RUN pip install kopf kubernetes pykube-ng[gcp]
CMD kopf run /src/handlers.py
