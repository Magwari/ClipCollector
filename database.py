from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal, Optional
from config import configRouter

import sqlite3
import os
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
CHUNK_SIZE = 1024*1024

connect = sqlite3.connect(os.path.join(configRouter.configparser.config['default']['data_path'], 'stream.db'))

#check database
check_cursor = connect.cursor()
check_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
table_list = [row[0] for row in check_cursor.fetchall()]
if 'tb_stream' not in table_list:
    logger.info('No stream table, creating new one...')
    check_cursor.execute("CREATE TABLE tb_stream (stream_id integer primary key, time text, video_name text, chat_name text)")
    connect.commit()
if 'tb_clip_time' not in table_list:
    logger.info('No clip_time table, creating new one...')
    check_cursor.execute("CREATE TABLE tb_clip_time (clip_id integer primary key, start_time integer, end_time integer, source text, tag text, stream_id integer)")
    connect.commit()
check_cursor.close()

#search DB
async def get_stream_list(connect):
    get_cursor = connect.cursor()
    get_cursor.execute("SELECT * FROM tb_stream ORDER BY time DESC")
    fields = [field[0] for field in get_cursor.description]
    return list(map(lambda row: dict(zip(fields,row)), get_cursor.fetchall()))

async def get_clip_list(connect, stream_id):
    get_cursor = connect.cursor()
    get_cursor.execute(f"SELECT * FROM tb_clip_time WHERE stream_id={stream_id} ORDER BY start_time DESC")
    fields = [field[0] for field in get_cursor.description]
    return list(map(lambda row: dict(zip(fields,row)), get_cursor.fetchall()))

#insert data into DB
async def data_insert(connect, table: str, data=tuple):
    insert_cursor = connect.cursor()
    if table == "tb_stream":
        insert_cursor.execute("INSERT INTO tb_stream (time, video_name, chat_name) VALUES (?,?,?)", data)
        lastrowid = insert_cursor.lastrowid
    elif table == "tb_clip_time":
        insert_cursor.execute("INSERT INTO tb_clip_time (start_time, end_time, source, tag, stream_id) VALUES (?,?,?,?,?)", data)
        lastrowid = insert_cursor.lastrowid
    connect.commit()
    insert_cursor.close()
    return lastrowid

#delete data from DB
async def data_delete(connect, table: str, id: int):
    delete_cursor = connect.cursor()
    if table == "tb_stream":
        delete_cursor.execute("DELETE FROM tb_stream WHERE stream_id=?", (str(id),))
    elif table == "tb_clip_time":
        delete_cursor.execute("DELETE FROM tb_clip_time WHERE clip_id=?", (str(id),))
    connect.commit()
    delete_cursor.close()

#edit data from DB
async def data_edit(connect, table: str, data=tuple):
    edit_cursor = connect.cursor()
    id = data[0]
    start_time = data[1]
    end_time = data[2]
    tag = data[4]
    if table == "tb_stream":
        #edit_cursor.execute("UPDATE tb_stream set tag=?, start=?, end=? WHERE id=?", (start_time, end_time, tag))
        pass
    elif table == "tb_clip_time":
        edit_cursor.execute("UPDATE tb_clip_time set tag=?, start_time=?, end_time=? WHERE clip_id=?", (str(tag), str(start_time), str(end_time), str(id)))
    connect.commit()
    edit_cursor.close()

#fastapi router
db = APIRouter()
db.connect = connect

#insert_form
class InsertForm(BaseModel):
    table: Literal["tb_stream", "tb_clip_time"]
    row: Optional[tuple] = None

@db.get("/db/stream")
async def api_get_stream_list(request: Request):
    result = await get_stream_list(db.connect)
    return json.dumps(result)

@db.get("/db/stream/{stream_id:int}")
async def api_get_clip_list(stream_id):
    result = await get_clip_list(db.connect, stream_id)
    return json.dumps(result)

@db.post("/db/insert")
async def api_db_edit(insertForm: InsertForm):
    await data_insert(db.connect, insertForm.table, insertForm.row)

@db.post("/db/edit")
async def api_db_edit(editForm: InsertForm):
    await data_edit(db.connect, editForm.table, editForm.row)

@db.get("/db/delete/stream/{stream_id:int}")
async def api_db_edit(stream_id):
    await data_delete(db.connect, 'tb_stream', stream_id)

@db.get("/db/delete/clip/{clip_id:int}")
async def api_db_edit(clip_id):
    await data_delete(db.connect, 'tb_clip_time', clip_id)