from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    raise HTTPException(status_code=400)
