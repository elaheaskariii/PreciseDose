from fastapi import FastAPI
from datetime import date

app = FastAPI()
#bjnki
@app.get("/age")
def calculate_age(birth_date: date):
    today = date.today()

    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return {
        "birth_date": birth_date,
        "age": age
    }