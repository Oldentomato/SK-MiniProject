import requests
from module.getApi import getApiKey
from module.format_convert import floorFormat, korean_money_to_int


def getModelResult(info):
    try:
        res = requests.post(getApiKey("MODEL_API_URL"), json={
            "J": info.get("자치구명"),
            "B": info.get("법적동명"),
            "Floor": floorFormat(info.get("층수")),
            "Area": info.get("면적"),
            "securityMoney": korean_money_to_int(info.get("보증금"))
        })

        if res.ok:
            resultStr = f"{res.json()['content']} 만원"
            return {"success": True, "content": resultStr}
        else:
            return {"success": False}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False}

    