import json
import sys
sys.path.insert(0, '/home/ubuntu/Saturday/backend')

from flask import Flask, request
app = Flask(__name__)

with app.test_request_context('/api/chat', method='POST', 
    data=json.dumps({"message": "hola"}), 
    content_type='application/json'):
    data = request.get_json(silent=True) or {}
    text_raw = data.get('message', data.get('text', ''))
    print(f"data keys: {list(data.keys())}")
    print(f"data: {data}")
    print(f"text_raw repr: {repr(text_raw)}")
    print(f"text_raw type: {type(text_raw)}")
    text = text_raw.strip() if text_raw else ''
    print(f"text after strip: {repr(text)}")

    from modules.input_validator import validate_message
    result = validate_message(text)
    print(f"validate_message result: {result}")
    print(f"validate_message return count: {len(result)}")
