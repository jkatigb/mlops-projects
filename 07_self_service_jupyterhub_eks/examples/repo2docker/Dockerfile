FROM python:3.11-slim
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
CMD ["jupyter", "lab"]
