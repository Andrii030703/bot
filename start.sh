#!/bin/bash

playwright install --with-deps chromium
python server_full_max.py
