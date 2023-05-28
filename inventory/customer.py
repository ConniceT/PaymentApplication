from main import redis , Product
from redis.exceptions import RedisError
import time

key='process_order'
Inv_group='inventory-group'


try:
    # Create the consumer group if it doesn't exist
    redis.xgroup_create(key, Inv_group, mkstream=True)
    group_exists = redis.xgroup_exists(key, Inv_group)
except RedisError as e:
    print(f"Failed to create consumer group: {e}")

while True:
    try:
        # Read from the consumer group
        results = redis.xreadgroup( Inv_group, key, {key:'>'}, None)
        print(results)
    except RedisError as e:
        print(f"Failed to read from consumer group{group_exists}: {e}")
    time.sleep(1)
