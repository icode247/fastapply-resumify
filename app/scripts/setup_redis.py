#!/usr/bin/env python
"""
Setup Redis with appropriate configuration for the application.
"""
import redis
import os
import logging
import argparse
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('redis-setup')

def setup_redis(redis_url, max_memory="25mb", eviction_policy="allkeys-lru"):
    """
    Configure Redis with appropriate memory settings
    
    Args:
        redis_url: Redis connection URL
        max_memory: Maximum memory to use (e.g., "25mb")
        eviction_policy: Eviction policy when memory is full
    """
    try:
        # Connect to Redis
        logger.info(f"Connecting to Redis at {redis_url}")
        redis_client = redis.from_url(redis_url)
        
        # Test connection
        redis_client.ping()
        logger.info("Connection successful")
        
        # Configure memory settings
        try:
            redis_client.config_set('maxmemory', max_memory)
            redis_client.config_set('maxmemory-policy', eviction_policy)
            logger.info(f"Set maxmemory to {max_memory} with policy {eviction_policy}")
        except redis.exceptions.ResponseError as e:
            logger.warning(f"Could not set Redis memory limits: {e}")
            logger.warning("This might be a managed Redis instance where CONFIG commands are restricted")
        
        # Show Redis info
        info = redis_client.info()
        memory_used = info.get('used_memory_human', 'Unknown')
        total_keys = info.get('db0', {}).get('keys', 0) if 'db0' in info else redis_client.dbsize()
        logger.info(f"Current Redis status: {memory_used} used, {total_keys} keys")
        
        return True
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return False
    except Exception as e:
        logger.error(f"Error setting up Redis: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Setup Redis for the Resumify API')
    parser.add_argument('--redis-url', help='Redis connection URL', 
                        default=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    parser.add_argument('--max-memory', help='Maximum memory for Redis', 
                        default=os.environ.get('REDIS_MAX_MEMORY', '25mb'))
    parser.add_argument('--eviction-policy', help='Redis eviction policy', 
                        default='allkeys-lru')
    
    args = parser.parse_args()
    
    if setup_redis(args.redis_url, args.max_memory, args.eviction_policy):
        logger.info("Redis setup completed successfully")
        return 0
    else:
        logger.error("Redis setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())