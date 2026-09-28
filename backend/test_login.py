import urllib.request
from urllib.error import HTTPError
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login', 
    method='POST', 
    headers={'Content-Type': 'application/json'}, 
    data=json.dumps({'email': 'patient@demo.smarthealth.local', 'password': 'Demo@Health2026'}).encode('utf-8')
)

try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8')}")
