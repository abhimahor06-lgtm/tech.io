import requests
BASE = 'http://localhost:5000/api'
print('Health', requests.get(BASE + '/health').json())
print('Schema', requests.get(BASE + '/health/schema').json())
headers = {'Authorization': 'Bearer invalid'}
for path in ['/teacher/1/dashboard', '/teacher/subjects', '/teacher/subjects/1/students', '/attendance/students']:
    r = requests.get(BASE + path, headers=headers)
    print(path, r.status_code, r.text)
