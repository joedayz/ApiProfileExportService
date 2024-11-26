import json
from _version import __version__
import socket


def reponse():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return json.dumps({
        'status': 'FAIL',
        'name': 'profile-export-service',
        'version': __version__,
        'ip': local_ip
        })


if __name__ == "__main__":
    print(reponse())
