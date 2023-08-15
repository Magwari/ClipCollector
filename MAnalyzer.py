import numpy as np
from utils import Analyzer

class MAnalyzer(Analyzer):
    def __init__(self, chat_path: str, size: int = 10, threshold: float = 0.7, **kwargs):
        super().__init__(chat_path=chat_path)
        self.list = list()
        self.temp = [int(self.start_time)]
        self.size = size
        self.threshold = threshold
        self.is_alerted = False
        self.last_alert = None
        self.alerted_timestamp = list()
        self.config = kwargs
    
    def add(self, item: int):
        self.temp.append(item)
        if len(self.temp) > self.size:
            self.temp.pop(0)
            
        time_interval = [self.temp[i+1]-self.temp[i] for i in range(len(self.temp)-1)]
        self.list.append(np.mean(time_interval))
        if len(self.list) < self.size:
            return False
        self.list.pop(0)
        return self.check()
            
    def check(self):
        massive_interval = (max(self.list)-min(self.list))/max(self.list) > self.threshold
        is_decrese = np.argmax(self.list)-np.argmin(self.list) < 0
        alert = massive_interval and is_decrese
        if self.is_alerted == False and alert == True:
            if self.last_alert and self.temp[-1] - self.last_alert < 30000:
                return False
            self.is_alerted = True
            self.last_alert = self.temp[-1]
            return True
        elif self.is_alerted == True and alert == False:
            self.is_alerted = False
            return False
        else:
            return False
        
    def analyze(self):
        for chat in self.chat_data[1:]:
            if 'ㅋ' not in chat['text']:
                continue
            alert = self.add(int(chat['tmi-sent-ts']))
            if alert:
                stream_timestamp_milisecond = int(chat['tmi-sent-ts']) - int(self.start_time)
                stream_timestamp = int(str(stream_timestamp_milisecond)[:-3])
                self.alerted_timestamp.append(stream_timestamp)