from fastapi import FastAPI, Request, HTTPException, Header, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
from io import BytesIO
from typing import Optional
import enum

from rtmp import serve_rtmp
from twitchApi import twitchApi
from config import configRouter
import database
import os

app = FastAPI()
app.include_router(twitchApi)
app.include_router(database.db)
app.include_router(configRouter)
app.running_rtmp_task = None
app.rtmp_data = {
    "isConnected": False
    }
app.queue = None

app.mount("/web/static", StaticFiles(directory="web/static"), name="static")
app.mount("/web/node_modules", StaticFiles(directory="web/node_modules"), name="node_modules")
templates = Jinja2Templates(directory="web/templates")

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    if twitchApi.profile.status and not app.running_rtmp_task:
        if app.queue:
            del app.queue
        app.queue = asyncio.Queue()
        rtmp_task = asyncio.create_task(serve_rtmp(port=configRouter.configparser.config['default']['rtmp_server_port'],
                                              access_token = twitchApi.profile.access_token,
                                              profile = twitchApi.profile.userdata,
                                              out_queue=app.queue))
        app.running_rtmp_task = rtmp_task
    return templates.TemplateResponse("main.html", {'request':request})

@app.get("/rtmp/start")
async def rtmp_server_start(request: Request):
    if app.running_rtmp_task:
        raise HTTPException(status_code=400, detail="RTMP server is already running.")
    if twitchApi.profile.status:
        if app.queue:
            del app.queue
        app.queue = asyncio.Queue()
        rtmp_task = asyncio.create_task(serve_rtmp(port=configRouter.configparser.config['default']['rtmp_server_port'],
                                              access_token = twitchApi.profile.access_token,
                                              profile = twitchApi.profile.userdata,
                                              out_queue=app.queue))
        app.running_rtmp_task = rtmp_task

    else:
        raise HTTPException(status_code=400, detail="Login Twitch first.")
    
@app.get("/rtmp/status")
async def rtmp_status(request: Request):
    return({"isRunning" : bool(app.running_rtmp_task)})

@app.websocket("/rtmp/status/ws")
async def rtmp_status_ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message" : "Connection start."})
    await websocket.send_json(app.rtmp_data)
    _connect_status = 1
    if not app.running_rtmp_task:
        await websocket.close(reason="RTMP Server is not started. Close WebSocket.")
        _connect_status = 0
    else:
        while _connect_status == 1:
            data = await app.queue.get()
            if data == "terminate":
                await websocket.close(reason="RTMP Server connection terminate.")
                _connect_status = 0
            else:
                app.rtmp_data = data
                await websocket.send_json(data)

@app.get("/rtmp/end")
async def rtmp_server_end(request: Request):   
    if not app.running_rtmp_task:
        raise HTTPException(status_code=400, detail="No running rtmp server.")
    app.running_rtmp_task.cancel()
    app.queue.put_nowait("terminate")
    app.running_rtmp_task = None

@app.get("/video")
async def video_endpoint(stream_id: Optional[str] = Header(default=None), video_range: Optional[str] = Header(default=None)):
    start, end = video_range.replace("times=", "").split("-")
    cursor = database.connect.cursor()
    cursor.execute("SELECT video_name FROM tb_stream WHERE stream_id=?", (stream_id))
    video_name = cursor.fetchone()[0]

    video_path = os.path.join(configRouter.configparser.config['default']['data_path'], "video", video_name)
    ffmpeg_command = f"{configRouter.configparser.config['default']['ffmpeg_path']} -ss {start} -to {end} -i {video_path} -frag_duration 3600 -c copy -f mp4 pipe:1"
    ffmpeg_process = await asyncio.create_subprocess_shell(ffmpeg_command,
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await ffmpeg_process.communicate()
    if stderr : 
        print(stderr.decode())

    def geterate_iter(data):
        dataio = BytesIO(data)
        while True:
            chunk = dataio.read(1024*1024)
            if not chunk:
                break
            yield chunk

    video_stream = geterate_iter(stdout)
    return StreamingResponse(iter(video_stream), media_type="video/mp4")
