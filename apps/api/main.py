from fastapi import FastAPI

app = FastAPI(title="LumiEdu API")


@app.get("/")
def hello_world() -> dict[str, str]:
    return {"message": "Hello World"}
