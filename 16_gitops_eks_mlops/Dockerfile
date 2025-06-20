FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts/train.py /app/train.py
COPY model.joblib /app/model.joblib
COPY server.py /app/server.py
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
