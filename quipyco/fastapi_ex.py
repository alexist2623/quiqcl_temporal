# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 13:45:30 2024

@author: alexi
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: list
    tax: float = None

@app.post("/items/")
async def create_item(item: Item):
    item.name = 'hello'
    item.price.append(90)
    return item