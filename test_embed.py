import urllib.request, json, urllib.error, os
os.environ['GEMINI_API_KEY'] = 'AIzaSyDowzVb7WiVNnVEL8nzVnOSJimZlQ2vDNo'
model = 'models/gemini-embedding-001'
api_key = os.environ['GEMINI_API_KEY']
url = 'https://generativelanguage.googleapis.com/v1beta/' + model + ':embedContent?key=' + api_key
payload = json.dumps({
    'model': model,
    'content': {'parts': [{'text': 'Python, Machine Learning, Django'}]},
    'taskType': 'SEMANTIC_SIMILARITY'
}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    values = data['embedding']['values']
    print('SUCCESS! Embedding length:', len(values), 'first 3 values:', values[:3])
except urllib.error.HTTPError as e:
    print('ERROR:', e.code, e.read().decode('utf-8'))
