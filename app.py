import json
from aiohttp import web
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from models import Session, Ad, close_orm, init_orm
from typing import Union


def get_http_error(err_cls, message: Union[str, dict, list]):
    error_message = json.dumps({"error": message})
    return err_cls(text=error_message, content_type="application/json")


app = web.Application()


async def orm_context(app: web.Application):
    print("start")
    await init_orm()
    yield
    print("finish")
    await close_orm()


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response


app.middlewares.append(session_middleware)
app.cleanup_ctx.append(orm_context)


async def get_Ad_by_id(ad_id, session: AsyncSession) -> Ad:
    ad = await session.get(Ad, ad_id)
    if ad is None:
        raise get_http_error(web.HTTPNotFound, "user not found")
    return ad


async def delete_Ad_by_id(ad: Ad, session: AsyncSession):
    await session.delete(ad)
    await session.commit()


async def add_Ad(ad: Ad, session: AsyncSession):
    session.add(ad)
    try:
        await session.commit()
    except IntegrityError as err:
        raise get_http_error(web.HTTPConflict, "user already exists")


class AdView(web.View):

    @property
    def ad_id(self):
        return int(self.request.match_info["ad_id"])

    async def get(self):
        ad = await get_Ad_by_id(self.ad_id, self.request.session)
        return web.json_response(ad.dict)

    async def post(self):
        json_data = await self.request.json()
        ad = Ad(**json_data)
        await add_Ad(ad, self.request.session)
        return web.json_response(ad.id_dict)

    async def delete(self):
        ad = await get_Ad_by_id(self.ad_id, self.request.session)
        await delete_Ad_by_id(ad, self.request.session)
        return web.json_response({"status": "deleted"})


app.add_routes(
    [
        web.post("/api", AdView),
        web.get("/api/{ad_id:[0-9]+}", AdView),
        web.delete("/api/{ad_id:[0-9]+}", AdView),
    ]
)

web.run_app(app, host='127.0.0.1', port=8080)