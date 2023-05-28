
from xml.dom import NotFoundErr
from fastapi import HTTPException
import os, time, asyncio, logging
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import HashModel, get_redis_connection
from starlette.requests import Request
import requests

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
    status: str  # pending, completed, refunded
  

    class Meta:
        database = redis


@app.get('/orders/{pk}')
async def get_order(pk: str):
    try:
        order = Order.get(pk)
        if order is None:
            raise HTTPException(status_code=404, detail=f"Order not found for ID: {pk}")
        return order
    except NotFoundErr:
        raise HTTPException(status_code=404, detail=f"Order not found for ID: {pk}")



@app.post('/orders')
async def create_order(request: Request, background_tasks: BackgroundTasks):
    # Fetch product information based on the product_id

    body= await request.json()
    product_id = body.get('id')

    if not product_id:
        raise HTTPException(400, "Product ID is missing in the request payload")

    response = requests.get(f'http://localhost:8000/products/{product_id}')

    print(response.content)
    print(response.status_code)

    if response.status_code == 200:
        product = response.json().get('products', {}).get(product_id)
        print(product)

        if not product:
            raise HTTPException(404, f"Product not found for ID: {product_id}")

        shipping_days = product.get('shipping_days')
    else:
        raise HTTPException(404, f"Product not found for ID: {product_id}")

    print(shipping_days)

    shipping_rates = {
        3: 10.0,
        5: 7.5,
        7: 5.0
    }
    

    shipping_rate = shipping_rates.get(shipping_days, 7.5)
    tax_rate = 0.15
    quantity = product["quantity"]
    price = product["price"]
    tax = price * tax_rate
    shipping = shipping_rate
    total = price + tax + shipping

    order = Order(
        order_id= product_id,
        price=price,
        tax=tax,
        shipping=shipping,
        total=total,
        quantity=quantity,
        status="pending"
    )

    if order is  None:
        raise HTTPException(status_code=400, detail="Product error, please check data")

    order.save()
    background_tasks.add_task(process_order, order)

    return order



async def process_order(order: Order):
    # Simulate a delay
    asyncio.sleep(5)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Cannot process order")
    order.status = "processed"
    order.save()
    redis.xadd('process_order', order.dict(), '*')
