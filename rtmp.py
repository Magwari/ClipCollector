import asyncio
from fastapi import WebSocket
from bitstring import BitStream, BitArray
import logging
import os
from datetime import datetime

from pyrtmp import StreamClosedException, RTMPProtocol
from pyrtmp.messages import SessionManager
from pyrtmp.messages.audio import AudioMessage
from pyrtmp.messages.command import NCConnect, NCCreateStream, NSPublish, NSCloseStream, NSDeleteStream
from pyrtmp.messages.data import MetaDataMessage
from pyrtmp.messages.protocolcontrol import WindowAcknowledgementSize, SetChunkSize, SetPeerBandwidth
from pyrtmp.messages.usercontrol import StreamBegin
from pyrtmp.messages.video import VideoMessage
from pyrtmp.misc.flvdump import FLVMediaType

import websockets
import database
from config import configRouter
from MAnalyzer import MAnalyzer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def pipe_init(stdin: asyncio.StreamWriter):
    stream = BitStream()
    stream.append(b'FLV')
    stream.append(BitStream(uint=1, length=8))
    stream.append(BitStream(uint=5, length=8))
    stream.append(BitStream(uint=9, length=32))
    stream.append(BitStream(uint=0, length=32))
    stdin.write(stream.bytes)
    await stdin.drain()

async def pipe_write(stdin: asyncio.StreamWriter, timestamp: int, payload: bytes, media_type: FLVMediaType):
    payload_size = len(payload)
    prev_tag_size = 11 + payload_size
    stream = BitStream()
    stream.append(BitArray(uint=int(media_type), length=8))
    stream.append(BitArray(uint=payload_size, length=24))
    stream.append(BitArray(uint=timestamp & 0x00FFFFFF, length=24))
    stream.append(BitArray(uint=timestamp >> 24, length=8))
    stream.append(BitArray(uint=0, length=24))
    stream.append(payload)
    stream.append(BitArray(uint=prev_tag_size, length=32))
    stdin.write(stream.bytes)
    await stdin.drain()

async def ffmpeg_controler(reader, writer, **kwargs):
    queue = kwargs.get('queue', None)
    session = SessionManager(reader=reader, writer=writer)
    flv = None
    try:
        logger.debug(f'Client connected {session.peername}')

        # do handshake
        await session.handshake()
        start_time = datetime.now().strftime('%Y%m%d%H%M%S')
        message = f"streaming started at {start_time}."
        file_name = f"live_{start_time}.mp4"
        
        # create flv file at temp
        # flv = FLVFile(os.path.join(file_path,'video', file_name))

        # create ffmpeg subprocess
        ffmpeg_command = f"{configRouter.configparser.config['default']['ffmpeg_src']} -i pipe:0 -c:v copy -c:a aac -f mp4 {configRouter.configparser.config['default']['data_path']}/video/{file_name}"
        ffmpeg_process = await asyncio.create_subprocess_shell(ffmpeg_command,
                                                               stdin=asyncio.subprocess.PIPE,
                                                               stdout=asyncio.subprocess.PIPE)
        await pipe_init(ffmpeg_process.stdin)
        queue.put_nowait(f"connected:{start_time}")

        # read chunks
        async for chunk in session.read_chunks_from_stream():
            message = chunk.as_message()
            logger.debug(f"Receiving {str(message)} {message.chunk_id}")
            if isinstance(message, NCConnect):
                session.write_chunk_to_stream(WindowAcknowledgementSize(ack_window_size=5000000))
                session.write_chunk_to_stream(SetPeerBandwidth(ack_window_size=5000000, limit_type=2))
                session.write_chunk_to_stream(StreamBegin(stream_id=0))
                session.write_chunk_to_stream(SetChunkSize(chunk_size=8192))
                session.writer_chunk_size = 8192
                session.write_chunk_to_stream(message.create_response())
                await session.drain()
                logger.debug("Response to NCConnect")
            elif isinstance(message, WindowAcknowledgementSize):
                pass
            elif isinstance(message, NCCreateStream):
                session.write_chunk_to_stream(message.create_response())
                await session.drain()
                logger.debug("Response to NCCreateStream")
            elif isinstance(message, NSPublish):
                session.write_chunk_to_stream(StreamBegin(stream_id=1))
                session.write_chunk_to_stream(message.create_response())
                await session.drain()
                logger.debug("Response to NSPublish")
            elif isinstance(message, MetaDataMessage):
                # Write meta data to file
                # flv.write(0, message.to_raw_meta(), FLVMediaType.OBJECT)

                # Write meta data to pipe
                await pipe_write(ffmpeg_process.stdin, 0, message.to_raw_meta(), FLVMediaType.OBJECT)
                await ffmpeg_process.stdin.drain()

            elif isinstance(message, SetChunkSize):
                session.reader_chunk_size = message.chunk_size
                logger.debug("Set Chunk Size")
            elif isinstance(message, VideoMessage):
                # Write video data to file
                # flv.write(message.timestamp, message.payload, FLVMediaType.VIDEO)

                # Write meta data to pipe
                await pipe_write(ffmpeg_process.stdin, message.timestamp, message.payload, FLVMediaType.VIDEO)

            elif isinstance(message, AudioMessage):
                # Write data data to file
                # flv.write(message.timestamp, message.payload, FLVMediaType.AUDIO)

                # Write meta data to pipe
                await pipe_write(ffmpeg_process.stdin, message.timestamp, message.payload, FLVMediaType.AUDIO)

            elif isinstance(message, NSCloseStream):
                pass
            elif isinstance(message, NSDeleteStream):
                pass
            else:
                logger.debug(f"Unknown message {str(message)}")

    except StreamClosedException as ex:
        logger.debug(f"Client {session.peername} disconnected!")
        message = f"streaming disconnected."
        ffmpeg_process.stdin.close()
        queue.put_nowait('disconnected')
        await ffmpeg_process.wait()

    finally:
        if flv:
            flv.close()

async def serve_chat(file_name, access_token, profile, channel_id=None):
    file_path = os.path.join(configRouter.configparser.config['default']['data_path'], 'chatLog')
    async with websockets.connect('ws://irc-ws.chat.twitch.tv:80') as websocket:
        await websocket.send('CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership')
        await websocket.send(f'PASS oauth:{access_token}')
        await websocket.send(f'NICK {profile["login"]}')
        if channel_id:
            await websocket.send(f'JOIN #{channel_id}')
        else:
            await websocket.send(f'JOIN #{profile["login"]}')

        while True:
            response = await websocket.recv()
            if response.startswith('PING'):
                await websocket.send('PONG :tmi.twitch.tv')
            elif 'PRIVMSG' in response:
                with open(os.path.join(file_path, file_name),'a', encoding='utf-8') as f:
                    f.write(response)

async def serve_rtmp(port=1935, access_token:str=None, profile=None, out_queue:asyncio.Queue=None):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: RTMPProtocol(controller=ffmpeg_controler, loop=loop, queue=queue), '127.0.0.1', port)
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')
    await server.start_serving()

    while True:
        message = await queue.get()
        if message.startswith('connected'):
            start_time = message.split(':')[1]
            stream_file_name = f"live_{start_time}.mp4"
            chat_file_name = f"chat_{start_time}.log"
            stream_id = await database.data_insert(database.connect, 'tb_stream', (start_time, stream_file_name, chat_file_name))
            chat_server = loop.create_task(serve_chat(chat_file_name, access_token, profile, channel_id="kumikomii"))
            rtmp_data = {
                "isConnected" : True,
                "stream_id" : stream_id,
                "start_time" : start_time,
                "stream_file_name" : stream_file_name,
                "chat_file_name" : chat_file_name
            }
            out_queue.put_nowait(rtmp_data)

        elif message.startswith('disconnected'):
            chat_server.cancel()
            rtmp_data = {
                "isConnected" : False,
                "stream_id" : None,
                "start_time" : None,
                "stream_file_name" : None,
                "chat_file_name" : None
            }
            out_queue.put_nowait(rtmp_data)

            if os.path.isfile(os.path.join(configRouter.configparser.config['default']['data_path'], 'chatLog', chat_file_name)):
                analyzer = MAnalyzer(os.path.join(configRouter.configparser.config['default']['data_path'], 'chatLog', chat_file_name))
                analyzer.analyze()
                for id, clip_time in enumerate(analyzer.alerted_timestamp):
                    start_time = max(0, clip_time+configRouter.configparser.config['default']['start_time_interval'])
                    end_time = clip_time+configRouter.configparser.config['default']['end_time_interval']
                    clip_id = await database.data_insert(database.connect, 'tb_clip_time', (start_time, end_time, analyzer.__class__.__name__, f"clip #{id}", stream_id))
            else:
                print("there is no chat log in streamed data.")