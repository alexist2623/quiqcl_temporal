# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 13:47:07 2024

@author: alexi
"""

import requests

url = "http://127.0.0.1:8000/items/"
item = {
    "name": "Foo",
    "description": "A very nice Item",
    "price": [35.4, 17.5],
    "tax": 3.5
}

response = requests.post(url, json=item)
print(response.json())