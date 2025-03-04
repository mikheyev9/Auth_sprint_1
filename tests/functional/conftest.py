import asyncio
import logging
import time
from logging import config as logging_config

import aiohttp
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from functional.settings import elasticsearch_settings, redis_settings, service_settings
from functional.utils.logger import LOGGING_CONFIG
from redis import asyncio as aioredis

# First configure logging
logging_config.dictConfig(LOGGING_CONFIG)
# Then create logger instance
logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client():
    es_client = AsyncElasticsearch(hosts=elasticsearch_settings.dsn)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name="aiohttp_client", scope="session")
async def aiohttp_client():
    aiohttp_client = aiohttp.ClientSession()
    yield aiohttp_client
    await aiohttp_client.close()


@pytest_asyncio.fixture(name="redis_client", scope="session")
async def redis_client():
    redis_client = aioredis.from_url(redis_settings.dsn)
    yield redis_client
    await redis_client.aclose()


@pytest_asyncio.fixture(name="redis_clean")
def redis_clean(redis_client):
    async def inner():
        await redis_client.flushall()
        count_keys = await redis_client.dbsize()
        logger.info(f"Redis готов к тестам. Кол-во ключей:{count_keys}.")

    return inner


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(aiohttp_client):
    """
    Получение запросов по endpoints с заданными параметрами.
    """

    async def inner(endpoint: str, query_data: dict = None):
        time_start = time.time()
        url = f"{service_settings.dsn}/api/v1/{endpoint}"
        async with aiohttp_client.get(url, params=query_data) as response:
            return (response.status, await response.json(), time.time() - time_start)

    return inner
