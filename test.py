import requests
try:
    requests.get('http://123.123.123.123:5000/',timeout=2)
except requests.exceptions.RequestException as e:
    pass
