from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import re
import sys, os
import joblib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.train import TrainModel
from router.route import model
from middleware import CustomMiddleware


app = FastAPI()

# FastAPI에 Redis 클라이언트 등록 (미들웨어에서 사용하기 위해)
@app.on_event("startup")
async def startup():
    if os.path.exists(modelPath := "./model/xgb_model.pkl"):
        app.state.model = joblib.load(modelPath)
    else:
        raise Exception("Not Found Model")


app.add_middleware(CustomMiddleware)

app.include_router(model, prefix='/api/model')

@app.get("/", status_code=200)
def root():
    return {"success": True, "message" : "health"}

