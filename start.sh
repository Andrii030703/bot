#!/bin/bash

playwright install --with-deps chromium
python server_saga_api_max.py
