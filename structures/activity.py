import json

class Activity:
    def __init__(self, activity: str):
        loaded_activity = json.loads(activity)
        self.application_id: int = loaded_activity['application_id']
        self.description: str = loaded_activity['description']
        self.details: dict = loaded_activity['details']