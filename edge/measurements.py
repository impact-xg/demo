from collections import deque

class Measurements:
    def __init__(self):
        self.records = deque(maxlen=25)
        
    def add_measurement(self, timestamp, data):
        self.records.append({timestamp: data})

    def get_measurements(self):
        if len(self.records) < 25:
            return None

        trace_data = []
        records_list = list(self.records)

        for i in range(0, 25, 5):
            group = records_list[i:i+5]
            group_dict = {}
            group_dict["timestamp"] = list(group[4].keys())[0]
            for record in group:
                group_dict.update(record)

            
            trace_data.append(group_dict)

        return trace_data

m = Measurements()
trace = m.get_measurements()

import json
print(json.dumps(trace, indent=4))