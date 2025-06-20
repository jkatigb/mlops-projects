FROM python:3.10-slim
WORKDIR /app
COPY scripts/train.py /app/train.py
COPY model.joblib /app/model.joblib
RUN pip install fastapi uvicorn scikit-learn joblib
COPY server.py /app/server.py
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
