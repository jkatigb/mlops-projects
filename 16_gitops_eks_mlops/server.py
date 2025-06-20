from fastapi import FastAPI
import joblib

model = joblib.load("model.joblib")
app = FastAPI()

@app.get("/predict")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    data = [[sepal_length, sepal_width, petal_length, petal_width]]
    pred = model.predict(data)[0]
    return {"class": int(pred)}
