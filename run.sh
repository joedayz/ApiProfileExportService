#!/usr/bin/env bash

export PYTHONPATH=/usr/lib/libreoffice/program:$PYTHONPATH
export URE_BOOTSTRAP=vnd.sun.star.pathname:/usr/lib/libreoffice/program/fundamentalrc

if command -v soffice &> /dev/null; then
  soffice --headless --writer --accept="socket,host=0.0.0.0,port=2002;urp;StarOffice.ServiceManager" &
  echo "Waiting for libreoffice..."
  sleep 3
  echo "Starting HTTP server..."
  python3 main.py "$@"
else
  echo "Failed to locate soffice binary, did you install libreoffice?"
fi
