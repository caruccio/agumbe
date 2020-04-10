FROM python:3.7
ADD src/operator.py /src/operator.py
RUN pip install kopf kubernetes pykube-ng[gcp]
CMD kopf run /src/operator.py
