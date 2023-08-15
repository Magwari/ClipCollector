from typing import Optional
import json

class Analyzer():
    def __init__(self, stream_path: Optional[str] = None, chat_path: Optional[str] = None):
        if stream_path:
            #open stream_file
            pass

        if chat_path:
            parser = ChatLogParser()
            self.start_time, self.chat_data = parser.read_chat(chat_path)
            pass
    
    def analyze(self):
        raise NotImplementedError

class ChatLogParser():
    def __init__(self):
        pass
    
    def read_chat(self, chat_path: str) -> tuple:
        with open(chat_path, 'r', encoding='UTF8') as f:
            start_time = None
            chat_data = list()
            for chat in f.readlines():
                if chat != '\n':
                    metadata_part, message_part = chat[1:-1].split(' PRIVMSG ')
                    metadata = dict([items.split('=') for items in metadata_part.split(';')])
                    if not start_time:
                        start_time=metadata['tmi-sent-ts']
                    message = message_part.split(':')[1]
                    metadata['text'] = message
                    chat_data.append(metadata)
            return (start_time, chat_data)
    
    def to_json(self, output_file: Optional[str]):
        if output_file:
            with open(output_file, 'w', encoding='UTF8') as f:
                f.write(json.dumps(self.chat_data))
        else:
            return json.dumps(self.chat_data)