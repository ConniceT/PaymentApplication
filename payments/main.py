
import logging
import os
import time
from collections import defaultdict

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import HashModel, get_redis_connection
from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app = FastAPI()

# Add middleware to handle cross-origin resource sharing (CORS) and port switching issues at the frontend.
app.add_middleware(
    CORSMiddleware, 
    allow_origins=['http://localhost:3000'],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,

)

load_dotenv()
redis_host = os.getenv("PAYMENT_HOST")
redis_port = int(os.getenv("PAYMENT_PORT"))
redis_password = os.getenv("PAYMENT_PASSWORD")

if redis_port is not None:
    port = int(redis_port )


# this should be another db - to be microservices
redis = get_redis_connection(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True
    )



class Order(HashModel):
    """
    Represents a product with attributes name, price, color, quantity, and discount.
    """
    order_id:str 
    price: float
    tax: float
    shipping: float
    total:float
    quantity: int
    status:str
  

    class Meta:
        database = redis


@app.post('/orders')
async def create_order(order: Order, background_tasks: BackgroundTasks):
    order.status = "created"
    background_tasks.add_task(process_order, order.order_id)
    return {"message": "Order created", "order_id": order.order_id, "order": order}


async def process_order(order_id: str):

     # Make an HTTP request to fetch the product information based on the order ID
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8001/products/{order_id}")
        if response.status_code == 200:
            products = response.json()
        else:
            raise Exception(f"Failed to retrieve product for order ID: {order_id}")
  
    order = Order(
    order_id=order_id,
    price=0.0,  # Replace with the actual price calculation logic
    tax=0.0,  # Replace with the actual tax calculation logic
    shipping=0.0,  # Replace with the actual shipping calculation logic
    total=0.0,  # Replace with the actual total calculation logic
    quantity=len(products),
    status="processed"

    )
    # Simulate a delay
    await time.sleep(5)
    redis.xadd(process_order, order.dict(), '*')




@app.get('/orders/{order_id}')
async def get_order(order_id: str):
    return Order.get(order_id)


@app.put('/orders/{order_id}/process')
async def process_order_endpoint(order_id: str, background_tasks: BackgroundTasks):
    # Process the order asynchronously
    background_tasks.add_task(process_order, order_id)
    return {"message": "Order processing initiated", "order_id": order_id}

@app.middleware("http")
async def log_request(request: Request, call_next):
    # Log incoming requests
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response
