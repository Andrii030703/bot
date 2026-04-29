#!/bin/bash

playwright install --with-deps chromium
python server_telegram_pro.py
