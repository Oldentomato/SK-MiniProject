from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.middleware import get_model
from src.train import TrainModel

model = APIRouter()

class ModelRequestForm(BaseModel):
    J: str
    B: str
    Floor: int 
    Area: float  
    securityMoney: int



@model.post("/getModelResult")
async def register_device(data: ModelRequestForm, model = Depends(get_model)):
    
    try:
        result = TrainModel.inferenceModel(xData={
            "자치구명": data.J,
            "법정동명": data.B,
            "층": data.Floor,
            "임대면적": data.Area,
            "보증금(만원)": data.securityMoney
        }, model=model)

        return {"success": True, "content": result}

    except Exception as e :
        return {"success": False, "msg": f"model inference Error: {e}"}