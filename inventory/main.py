import os
import logging
from dotenv import load_dotenv
from typing import Union, List
from collections import defaultdict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
import redis

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


redis = get_redis_connection(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True
    )



class Product(HashModel):
    """
    Represents a product with attributes name, price, color, quantity, and discount.
    """
    name:str 
    price: float
    color: str
    quantity: int
    discount: float
    shipping_days: float
    discounted_price: float = 0.00
    
    


    class Meta:
        database = redis


@app.get('/products')
def all():
    """
    Retrieve all product primary keys.
    """
    return [format(product_id) for product_id in Product.all_pks()]


def format(product_id: str):
    product= Product.get(product_id)
    return{
         "id": product.pk,
        "name": product.name,
        "price": product.price,
        "color": product.color,
        "quantity": product.quantity,
        "discount": product.discount,
        "shipping_days": product.shipping_days
        
      
    }



@app.get('/products/{product_id}')
def get_product(product_id: str):
    """
    Retrieve a product or multiple products by their ID(s).
    """

    product_id_list = product_id.split(',')
    products_store= defaultdict(str)
    prod_count=0

    if len(product_id_list) == 0:
        raise HTTPException(status_code=400, detail="No product ID provided")

    for prod_id in product_id_list:
        try:
            product = Product.get(prod_id)
            products_store[prod_id]= product
            prod_count+=1
        except KeyError:
            pass

    if prod_count > 0:
        # At least one product was successfully deleted
        return {
            "message": f"{prod_count} products retrieved successfully",
            "status": status.HTTP_200_OK,
            "products": products_store
        }
    else:
            # No products were found for retrivial
        raise HTTPException(status_code=404, detail="Products not found")
    

@app.post('/products')
def create_products(products: Union[Product, List[Product]]):
    """
    Create one or multiple products.1`  
    """
    if isinstance(products, list):
        for product in products:
            if product.discount > 0.00:
                # Calculate discounted price if a discount is provided
                product.discounted_price = product.price - (product.price * product.discount)
            product.save()
        return {"message": "Products created successfully",
                "products": products
        }
    else:
        if products.discount > 0.00:
            # Calculate discounted price if a discount is provided
            products.discounted_price = products.price - (products.price * products.discount)
        products.save()
        return {"message": "Product created successfully", 
         "product": products}


@app.delete('/products/{product_id}')
def delete_product(product_id:str):
    """
    Delete one or many products by their IDs.
    """
    ids = product_id.split(',')  # Split the string of IDs into a list
    deleted_count = 0

    for prod_id in ids:
        try:
            prod_id= prod_id.strip()
            Product.delete(prod_id)  # Remove any whitespace around the ID
            deleted_count += 1
        except KeyError:
            pass

    if deleted_count > 0:
        # At least one product was successfully deleted
        return {
            "message": f"{deleted_count} products deleted successfully",
            "status": status.HTTP_204_NO_CONTENT
        }
    else:
        # No products were found for deletion
        raise HTTPException(status_code=404, detail="Products not found")


@app.delete('/products')
def delete_all_products():
    """
    Delete all products.
    """
    # Get all product IDs
    all_product_ids = Product.all_pks()
    
    deleted_count = 0

    for product_id in all_product_ids:
        try:
            Product.delete(product_id)
            deleted_count += 1
        except KeyError:
            pass

    if deleted_count > 0:
        # Products were successfully deleted
        return {
            "message": f"All products deleted successfully",
            "status": status.HTTP_204_NO_CONTENT
        }
    else:
        # No products were found for deletion
        raise HTTPException(status_code=404, detail="No products found")

