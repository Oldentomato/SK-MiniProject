from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # token = request.headers["Authorization"].split(' ')[1] # 'Bearer TOKEN'에서 TOKEN 부분만 추출

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"

        return response



def get_model(request: Request):
    return request.app.state.model