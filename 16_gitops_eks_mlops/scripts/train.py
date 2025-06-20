import joblib
import mlflow
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

mlflow.set_experiment("demo")

X, y = load_iris(return_X_y=True)
model = LogisticRegression(max_iter=200)

with mlflow.start_run():
    model.fit(X, y)
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_metric("accuracy", model.score(X, y))
    joblib.dump(model, "model.joblib")
