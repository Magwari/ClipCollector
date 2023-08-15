import configparser
import os
import shutil
from fastapi import Request, APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


class ConfDataFormat(BaseModel):
    data_path : str
    client_id : str
    client_secret : str
    rtmp_server_autostart : str
    rtmp_server_port : str
    ffmpeg_path : str
    start_time_interval : str
    end_time_interval : str
    

class Config():
    def __init__(self):
        PATH = os.path.dirname(__file__)
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(PATH, 'conf.ini'))
    
    def setConfig(self, input_data):
        check_path_result = self.check_path(input_data['data_path'])
        if not check_path_result['isValid'] :
            return {
                'isValid' : False,
                'invalidData' : 'data_path',
                'detail' : check_path_result['detail']
            }

        check_client_info_result = self.check_client_info(input_data['client_id'], input_data['client_secret'])
        if not check_client_info_result['isValid'] :
            return {
                'isValid' : False,
                'invalidData' : 'client_info',
                'detail' : check_client_info_result['detail']
            }
        
        check_ffmpeg_info_result = self.check_ffmpeg_info(input_data['ffmpeg_path'])
        if not check_ffmpeg_info_result['isValid'] :
            return {
                'isValid' : False,
                'invalidData' : 'ffmpeg_path',
                'detail' : check_ffmpeg_info_result['detail']
            }
        
        #confDataFormat -> conf.
        self.config.read_dict({
            'default' : input_data
        })
        return {
            'isValid' : True
        }

    def check_path(self, path) -> dict:
        #check path is exist
        if os.path.exists(path):
            return {'isValid' : True}
        else:
            return {
                'isValid' : False,
                'invalidData' : 'data_path',
                'detail' : "Path is not exist."
            }

    def check_client_info(self, client_id, client_secret) -> dict:
        #check auth is valid. find something proper Twitch API.
        return {'isValid' : True}

    def check_ffmpeg_info(self, command) -> dict:
        #check path is ffmpeg.
        if shutil.which(command):
            return {'isValid' : True}
        else:
            return {
                'isValid' : False,
                'invalidData' : 'ffmpeg_path',
                'detail' : "ffmpeg is not found. Check your environment path and input value."
            }
        
configRouter = APIRouter()
configRouter.configparser = Config()

@configRouter.post("/conf/set", tags=["config"])
def set_config(confData: ConfDataFormat):
    print(dict(confData))
    input_data = {
        'data_path' : confData.data_path,
        'client_id' : confData.client_id,
        'client_secret' : confData.client_secret,
        'rtmp_server_autostart' : True if confData.rtmp_server_autostart=='True' else False,
        'rtmp_server_port' : int(confData.rtmp_server_port),
        'ffmpeg_path' : confData.ffmpeg_path,
        'start_time_interval' : int(confData.start_time_interval),
        'end_time_interval' : int(confData.end_time_interval),
    }
    return configRouter.configparser.setConfig(input_data)

@configRouter.get("/conf", tags=["config"])
def get_config(request: Request):
    return dict(configRouter.configparser.config['default'])