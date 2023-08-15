from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from config import configRouter

import requests

class Profile():
    def __init__(self):
        self.logout()
    
    def login(self, access_token, userdata):
        self.status = True
        self.access_token = access_token
        self.userdata = userdata

    def logout(self):
        self.status = False
        self.access_token = None
        self.userdata = None

twitchApi = APIRouter()
twitchApi.profile = Profile()

@twitchApi.get("/login", tags=["twtichApi"])
def login(request: Request):
    twitch_authorize_url = f"https://id.twitch.tv/oauth2/authorize?" \
        f"client_id={configRouter.configparser.config['default']['client_id']}&" \
        f"redirect_uri={request.base_url._url + 'auth'}&" \
        "response_type=code&" \
        "scope=user:read:email+chat:read"
    return RedirectResponse(url=twitch_authorize_url)

@twitchApi.get("/auth", tags=["twtichApi"])
def authentication(request: Request, code: str = "default", error = None):
    if error:
        raise HTTPException(status_code=401, detail="Access denied.")
    
    if code == "default":
        raise HTTPException(status_code=406, detail="Not allowed request.")
    
    oauth2_data = {
            "client_id": configRouter.configparser.config['default']['client_id'],
            "client_secret": configRouter.configparser.config['default']['client_secret'],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": request.base_url._url
            }

    get_token_response = requests.post("https://id.twitch.tv/oauth2/token", data=oauth2_data)
    if get_token_response.status_code == 200:
        access_token = get_token_response.json()["access_token"]
        get_user_response = requests.get(url="https://api.twitch.tv/helix/users",
                                 headers={"Authorization": f"Bearer {access_token}",
                                          "Client-Id": configRouter.configparser.config['default']['client_id']})
        if get_user_response.status_code == 200:
            twitchApi.profile.login(access_token, get_user_response.json()['data'][0])
            return RedirectResponse(url="/")
        else:
            raise HTTPException(status_code=403, detail="Get error while requesting userdata to Twitch.")
    else:
        raise HTTPException(status_code=get_token_response.status_code, detail=get_token_response.text)

@twitchApi.get("/profile", tags=["twtichApi"])
def get_profile(requests: Request):
    return twitchApi.profile.__dict__

@twitchApi.get("/logout", tags=["twtichApi"])
def logout(requests: Request):
    twitchApi.profile.logout()
    return RedirectResponse(url="/")