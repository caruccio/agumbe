FROM python:3.7-slim
RUN mkdir -p /src/agumbe/logs /src/agumbe/conf
RUN useradd -m -d /src/agumbe -s /sbin/nologin -u 200 agumbe
RUN pip install kopf kubernetes
ADD src/operator.py /src/agumbe/operator.py
RUN chown -R agumbe:agumbe /src/agumbe
WORKDIR /src/agumbe
USER agumbe
CMD kopf run --standalone operator.py 2>&1 | tee logs/application.log
