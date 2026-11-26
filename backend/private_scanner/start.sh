#!/bin/sh
set -eu
freshclam --stdout
freshclam --daemon --checks=12 --stdout
exec uvicorn server:app --host 0.0.0.0 --port 8080 --workers 1 --no-access-log
