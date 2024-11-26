from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import cgi
# from urllib.parse import parse_qs
import os
import convert
import io
import socket
import zipfile
# import re
from _version import __version__


def append_member(zip_file, member):
    with zipfile.ZipFile(zip_file, mode="a") as archive:
        archive.write(member)


class Server(BaseHTTPRequestHandler):

    def _set_headers(self, contentType='application/json', status=200):
        self.send_response(status)
        self.send_header('Content-type', contentType)
        self.send_header(
                'Access-Control-Allow-Origin',
                'http://localhost:3000'
                )
        self.end_headers()

    def do_GET(self):

        if self.path == "/":
            self._set_headers('text/html')
            content = open('index.html', 'rb').read()
            self.wfile.write(content)
        elif self.path == '/health':
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            response = json.dumps({
                'Status': 'ok',
                'Name': 'profile-export-service',
                'Version': __version__,
                'Ip': local_ip
            })
            response = bytes(response, 'utf-8')
            self._set_headers()
            self.wfile.write(response)
        elif self.path == '/health/':
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            response = json.dumps({
                'Status': 'ok',
                'Name': 'profile-export-service',
                'Version': __version__,
                'Ip': local_ip
            })
            response = bytes(response, 'utf-8')
            self._set_headers()
            self.wfile.write(response)
        else:
            self._set_headers("text/html", 404)
            content = open('notfound.html', 'rb').read()
            self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header(
                'Access-Control-Allow-Origin',
                'http://localhost:3000'
                )
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, Authorization"
                )
        self.end_headers()

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        # length = int(self.headers.get('content-length'))

        # Exit if the content type isn't correct
        if ctype != 'multipart/form-data':
            self.send_response(
                    400,
                    "Content type must be 'multipart/form-data'"
                    )
            self.end_headers()
            return

        # Parse request
        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
        postvars = cgi.parse_multipart(self.rfile, pdict)
        profile = postvars.get("profile")
        template = postvars.get("template")

        if template:
            template = io.BytesIO(template[0])
        else:
            template = open("templates/main.odt", "rb")

        if profile and len(profile) == 1:

            # Read files
            profile = json.loads(profile[0])
            # print("DEBUG_PROFILE: ", json.dumps(profile))

            # Convert input to output
            convert.output(profile, template)

            # Write converted file back
            self._set_headers("application/pdf")
            with open('output.pdf', 'rb') as file:

                # Read the file and send the contents
                self.wfile.write(file.read())
        elif profile and len(profile) > 1:
            for p in profile:
                local = json.loads(p)
                filename = local.get("name") + ".pdf"
                convert.output(local, template, filename)
                append_member("output.zip", filename)
                os.remove(filename)

            self._set_headers("application/zip")
            with open('output.zip', 'rb') as output:
                self.wfile.write(output.read())
            os.remove('output.zip')

        else:
            self.send_response(
                    400,
                    "Please provide a profile in request"
                    )
            self.end_headers()


def run(host_name, port):
    webServer = HTTPServer((host_name, port), Server)
    print("Server started http://%s:%s" % (host_name, port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
