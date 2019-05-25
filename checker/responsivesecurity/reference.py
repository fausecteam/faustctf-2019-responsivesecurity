import requests

def store(endpoint, userid, path, data):
    url = endpoint + "/storage/" + userid + path
    requests.put(url, data, verify=False).raise_for_status()
    return url

