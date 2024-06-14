from fastapi import FastAPI

from routers import auth, product
from utilites import constants
from middleware import langchain
import sys

# Initialize app
app = FastAPI()
app.include_router(auth.router)
app.include_router(product.router)

constants.init()


