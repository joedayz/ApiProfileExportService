# Quadim-ProfileExportService

A module to support export of Quadim profiles for a selected UI-template to pdf-files.  The intention is to build this as a standalone Docker image to simplify deployments and vertical scaling when needed.

## Requirements

- Python 3 version >= `3.6`
- LibreOffice >= `7`

## Installation


Clone this repo, and install `requirements.txt`:

```
pip install -r requirements.txt
```

### Arch and latest python

After [PEP 668](https://peps.python.org/pep-0668/) we need to install packages
in a virtual env to get up and running locally:

I'm using [uv](https://github.com/astral-sh/uv) here, but you can use another
implementation if needed, or pass the flag `--break-system-packages` which is
not recommended

```sh
uv venv # setup venv
source .venv/bin/activate # activate venv
uv pip install -r requirements.txt  # install deps
```

Then you should almost be good to go, but you need to set a venv flag in config file as well
```sh
vim .venv/pyvenv.cfg
```
```cfg
include-system-site-packages = true
```

We need this flag to locate packages outside venv

## Running

To start both LibreOffice and HTTP server run:

```
./run.sh
```
The server should now be listening for POST requests sent to it.

The request needs to take the form of `multipart/form-data`, where `profile` is
a Quadim user profile in JSON format, and `template` is an odt file. An example
request would look like this:

```
curl -F 'profile=@profiles/daniel.json' -F 'template=@templates/cv.odt' http://localhost:8080 --output mycv.pdf
```

You can pass multiple profiles to the service, it'll return a zip file if
supplied with more than one profile

```
curl -F 'profile=@profiles/daniel_no.json' -F 'profile=@profiles/brad.json' -F 'template=@templates/main.odt' ec2-3-70-14-87.eu-central-1.compute.amazonaws.com:8080 --output mycv.zip
```

result:

```zip
" Browsing zipfile mycv.zip
Daniel Berg.pdf
Brad.pdf
```

### Environment and python main.py

If you need for some reason to start the python service manually, not via the
run script, make sure to include these two environment variables:

```
export PYTHONPATH=/usr/lib/libreoffice/program:$PYTHONPATH
export URE_BOOTSTRAP=vnd.sun.star.pathname:/usr/lib/libreoffice/program/fundamentalrc
```

## Template syntax

See the document [TEMPLATE.md](TEMPLATE.md), or refer to https://github.com/christopher-ramirez/secretary

## Deploying

We use github actions to deploy instances, `DEV`, `QA`, and `PROD`. You can view the action [here](https://github.com/quadimai/Quadim-ProfileExportService/blob/main/.github/workflows/aws.yml).

## Public IP DNS and instance health

You can access the various instances using these URLs

### Devtest
```shell
curl http://PdfFargateALB-4705873.eu-central-1.elb.amazonaws.com:8080/health
# {"Status": "ok", "Name": "profile-export-service", "Version": "0.2", "Ip": "172.17.0.2"}%
```
### Production

We're using a load-balancer, so to talk to the service, and check its status
use URL: `PdfFargateALB-746176996.eu-north-1.elb.amazonaws.com:8080/health`


Check that `prod` is working:
```shell
curl pdffargateALB-746176996.eu-north-1.elb.amazonaws.com:8080/health
# {"Status": "ok", "Name": "profile-export-service", "Version": "0.2", "Ip": "172.31.46.8"}%
```
## Docker

To use this program effectively a Dockerfile has been included. To build an image cd into root and:

```
sudo docker build -t my-export-service .
```

Then run the image:
```
sudo docker run -tp 8080:8080 my-export-service
```

Then you can run curl commands as usual, targeting `localhost`


### Hostname and port

The python file `main.py` can take hostname and port optional arguments for the
http server. To tell docker to use a different port:

```Dockerfile
# Setting the port to 2345
CMD ["/app/run.sh", "0.0.0.0", "2345"]
```
The libreoffice server has a hardcoded address, but since its never communicated to directly I don't think this'll be an issue

- https://github.com/quadimai/Quadim-ProfileExportService/blob/cf9e7acb1fd3877bb2c14c1cf7e499b858be7725/convert.py#L52


## Troubleshooting

### Temporary file

This program relies on storing a temporary file in `/tmp/cvtmp.odt`, make sure
that the user running the program has write permissions to `/tmp`

No checks are currently done to ensure presence of any files, and the program
will simply throw an error. This will be improved later.

### Versions list

List of versions that I used to develop this program

- Arch linux: `6.7.6-arch1-1`
- Python: `Python 3.11.7`
- LibreOffice: `LibreOffice 24.2.0.3 420(Build:3)`
- Jinja2: `3.1.3`
- markdown2: `2.4.13`

### Viewing logs in development

Not sure, I did most of my debugging on prod, and the images deploy at the same
time, but I'm assuming its in cloudwatch as well, but there are no configured
groups yet.

### Viewing logs in production

To view logs you need to log into aws, and navigate to `CloudWatch -> Logs -> Log groups -> /ecs/PdfTask`

![image](https://user-images.githubusercontent.com/4509009/215481571-06a4191c-4ed8-4bee-a252-49a85ab52830.png)

Usually its the top log stream, but we load balance so thats not a guarantee, just find the one that actively responds to requests
