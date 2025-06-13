import redis.asyncio as redis


async def test_redis():
    pool = redis.ConnectionPool.from_url('redis://redis.turing.orb.local:6379/0?decode_responses=True')
    r = redis.Redis.from_pool(pool)
    await r.set('foo', 'bar')
    assert await r.get('foo') == 'bar'
    await r.delete('foo')
    assert await r.get('foo') is None
    await r.aclose()
    await pool.disconnect()