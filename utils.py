import json


def get_response_message(data):
    return json.dumps({"message": data})
