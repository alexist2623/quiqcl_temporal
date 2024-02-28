# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 13:47:07 2024

@author: alexi
"""

import requests

url = "http://127.0.0.1:8000/call/"
item = {
    "key": 1234,
    "action": "call",
    "name": "ad9912_0.do_print",
    "args": ["api response"],
    "kwargs": {}
}

response = requests.post(url, json=item)
print(response.json())