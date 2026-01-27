import asyncio

import aiohttp

async def main():

    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://127.0.0.1:8080/api',
            json={'id': 10, 'title': 'Test Ad', 'content': 'This is a test advertisement.', 'owner': 'user15'},
        ) as response:
            print(response.status)
            print(await response.json())

asyncio.run(main())

# async def main():

#     async with aiohttp.ClientSession() as session:
#         async with session.get(
#             'http://127.0.0.1:8080/api/10',
#         ) as response:
#             print(response.status)
#             print(await response.json())

# asyncio.run(main())

# async def main():

#     async with aiohttp.ClientSession() as session:
#         async with session.delete(
#             'http://127.0.0.1:8080/api/10',
#         ) as response:
#             print(response.status)
#             print(await response.json())

# asyncio.run(main())