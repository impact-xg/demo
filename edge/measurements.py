from collections import deque

class Measurements:
    def __init__(self):
        #self.records = deque(maxlen=25)
        self.records = deque(maxlen=5)
        self.maxlen=5
        
    def add_measurement(self, timestamp, data):
        self.records.append({timestamp: data})

    def get_measurements(self):
        if len(self.records) < self.maxlen:
            return None

        trace_data = []
        records_list = list(self.records)

        #for i in range(0, 25, 5):
        for i in range(0, self.maxlen, 5):
            group = records_list[i:i+5]
            group_dict = {}
            group_dict["timestamp"] = int(list(group[4].keys())[0])
            for record in group:
                group_dict.update(record)

            
            trace_data.append(group_dict)

        return trace_data

m = Measurements()
trace = m.get_measurements()

import json
print(json.dumps(trace, indent=4))