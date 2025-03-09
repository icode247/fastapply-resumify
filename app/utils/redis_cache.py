# import redis
# import json
# import hashlib
# from functools import wraps
# from flask import request
# import os
# import logging

# # Initialize Redis client with sensible defaults
# redis_url = os.environ.get('REDIS_URL')
# redis_client = redis.from_url(redis_url)
# logger = logging.getLogger(__name__)

# # Set default expiration time (30 minutes)
# DEFAULT_EXPIRATION = 1800

# # Memory management settings (maximum 25MB for cache to leave buffer)
# MAX_MEMORY_POLICY = "allkeys-lru"  # Least Recently Used eviction
# MAX_MEMORY_LIMIT = "25mb"

# # Configure Redis for memory constraints
# try:
#     redis_client.config_set('maxmemory', MAX_MEMORY_LIMIT)
#     redis_client.config_set('maxmemory-policy', MAX_MEMORY_POLICY)
# except redis.exceptions.ResponseError:
#     # This might fail in some managed Redis services where CONFIG is disabled
#     logger.warning("Could not set Redis memory limits. This might be a managed instance.")


# def generate_cache_key(route, data=None):
#     """Generate a cache key based on route and request data"""
#     if data is None:
#         data = request.get_json() if request.is_json else request.form.to_dict()
    
#     # Create a string representation of the data
#     data_str = json.dumps(data, sort_keys=True) if data else ""
    
#     # Generate a hash for the key
#     key = f"{route}:{hashlib.md5(data_str.encode()).hexdigest()}"
#     return key


# def cache_response(expiration=DEFAULT_EXPIRATION):
#     """Decorator to cache API responses"""
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             # Skip caching for health check and similar endpoints
#             if request.path == '/health':
#                 return f(*args, **kwargs)
            
#             # Get request data
#             if request.is_json:
#                 data = request.get_json()
#             else:
#                 data = request.form.to_dict()
            
#             # Generate cache key
#             cache_key = generate_cache_key(request.path, data)
            
#             # Try to get from cache
#             cached_response = redis_client.get(cache_key)
#             if cached_response:
#                 try:
#                     return json.loads(cached_response)
#                 except json.JSONDecodeError:
#                     # If cached response is not JSON, return it as-is
#                     return cached_response
            
#             # Execute the function and cache the result
#             response = f(*args, **kwargs)
            
#             # Only cache successful responses
#             if hasattr(response, 'status_code') and response.status_code == 200:
#                 try:
#                     # If it's a Flask response, we need to get the data
#                     if hasattr(response, 'get_json'):
#                         cache_data = json.dumps(response.get_json())
#                     elif hasattr(response, 'get_data'):
#                         cache_data = response.get_data().decode('utf-8')
#                     else:
#                         cache_data = json.dumps(response)
                        
#                     # Cache the response
#                     redis_client.setex(cache_key, expiration, cache_data)
#                 except (TypeError, json.JSONDecodeError):
#                     logger.warning(f"Could not cache response for {request.path}")
            
#             return response
#         return decorated_function
#     return decorator


# def invalidate_cache(route=None, data=None):
#     """Invalidate cache for a specific route or pattern"""
#     if route and data:
#         # Invalidate specific key
#         key = generate_cache_key(route, data)
#         redis_client.delete(key)
#     elif route:
#         # Invalidate all keys for a route using pattern matching
#         pattern = f"{route}:*"
#         keys = redis_client.keys(pattern)
#         if keys:
#             redis_client.delete(*keys)
#     else:
#         # This is dangerous, so log it
#         logger.warning("Invalidating all cache keys")
#         redis_client.flushall()


# def get_cache_stats():
#     """Get Redis cache statistics"""
#     try:
#         info = redis_client.info()
#         memory_used = info.get('used_memory_human', 'Unknown')
#         keys = info.get('db0', {}).get('keys', 0) if 'db0' in info else redis_client.dbsize()
#         return {
#             'memory_used': memory_used,
#             'keys': keys,
#             'max_memory': MAX_MEMORY_LIMIT,
#             'eviction_policy': MAX_MEMORY_POLICY
#         }
#     except:
#         return {
#             'status': 'error',
#             'message': 'Could not retrieve Redis cache statistics'
#         }