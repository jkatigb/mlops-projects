from fastapi import FastAPI
import joblib

model = joblib.load("model.joblib")
app = FastAPI()

@app.get("/predict")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    """
    Predicts the class label for an iris flower based on its sepal and petal measurements.
    
    Parameters:
        sepal_length (float): Length of the sepal in centimeters.
        sepal_width (float): Width of the sepal in centimeters.
        petal_length (float): Length of the petal in centimeters.
        petal_width (float): Width of the petal in centimeters.
    
    Returns:
        dict: A JSON-compatible dictionary containing the predicted class label under the key "class".
    """
    data = [[sepal_length, sepal_width, petal_length, petal_width]]
    pred = model.predict(data)[0]
    return {"class": int(pred)}
