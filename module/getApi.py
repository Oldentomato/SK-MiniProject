from dotenv import load_dotenv
import os 

load_dotenv(dotenv_path=".env", override=True, verbose=True)

def getApiKey(apiName):
    try:
        key = os.getenv(apiName)
    except:
        raise Exception("No Api Key!")
    
    return key