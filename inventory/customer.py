from main import redis , Product
from redis.exceptions import RedisError
import time

key='order-completed'
Inv_group='inventory-group'


try:
    redis.xgroup_create(key, Inv_group, mkstream=True)
except RedisError as e:
    print(f"Failed to create consumer group: {e}")


try:
    results = redis.xreadgroup( Inv_group,key, {key:'.'}, None)
except RedisError as e:
    print(f"Failed to read from consumer group: {e}")
time.sleep(1)
