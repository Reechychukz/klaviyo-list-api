from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY")
KLAVIYO_LIST_ID = os.getenv("KLAVIYO_LIST_ID")
KLAVIYO_URL = os.getenv("KLAVIYO_URL")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.solesme.com", "https://solesmes.webflow.io/"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class SubscribeRequest(BaseModel):
    email: str

@app.options("/subscribe")
async def options_handler():
    return JSONResponse(content={}, headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST"})

@app.post("/subscribe")
def subscribe_email(request: SubscribeRequest):
    """Subscribe an email to Klaviyo with single opt-in."""
    payload = {
        "data": {
            "type": "subscription",
            "attributes": {
                "profile": {
                    "data": {
                        "type": "profile",
                        "attributes": {
                            "email": request.email,
                            "subscriptions": {
                                "email": {
                                    "marketing": {
                                        "consent": "SUBSCRIBED"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "relationships": {
                "list": {
                    "data": {
                        "type": "list",
                        "id": KLAVIYO_LIST_ID
                    }
                }
            }
        }
    }

    headers = {
        "accept": "application/vnd.api+json",
        "revision": "2025-01-15",
        "content-type": "application/vnd.api+json"
    }

    response = requests.post(
        f"{KLAVIYO_URL}?company_id={KLAVIYO_API_KEY}",
        json=payload,
        headers=headers
    )

    if response.status_code not in [200, 202]:
        try:
            error_detail = response.json()  # Check if response contains JSON
        except requests.exceptions.JSONDecodeError:
            error_detail = response.text  # If not JSON, return raw text
        
        raise HTTPException(status_code=response.status_code, detail=error_detail)

    try:
        return response.json()  # Only return JSON if present
    except requests.exceptions.JSONDecodeError:
        return {"message": "Subscription successful, but response was empty."}
