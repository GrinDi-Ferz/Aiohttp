import json
from aiohttp import web
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Session, Ad, close_orm, init_orm
from typing import Union
from pydantic import BaseModel, ValidationError, constr, EmailStr

routes = web.RouteTableDef()

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

class AdCreate(BaseModel):
    title: constr(min_length=3, max_length=100)
    content: constr(min_length=10)
    owner: constr(min_length=3)

class AdView(web.View):

    @property
    def ad_id(self):
        return int(self.request.match_info["ad_id"])

    async def get(self):
        ad = await get_Ad_by_id(self.ad_id, self.request.session)
        return web.json_response(ad.dict)

    async def post(self):
        json_data = await self.request.json()
        try:
            ad_data = AdCreate(**json_data)
        except ValidationError as e:
            return get_http_error(web.HTTPUnprocessableEntity, e.errors())

        ad = Ad(**ad_data.dict())
        await add_Ad(ad, self.request.session)
        return web.json_response(ad.id)

    async def delete(self):
        ad = await get_Ad_by_id(self.ad_id, self.request.session)
        await delete_Ad_by_id(ad, self.request.session)
        return web.json_response({"status": "deleted"})

    async def patch(self):
        ad = await get_Ad_by_id(self.ad_id, self.request.session)
        json_data = await self.request.json()

        try:
            ad_data = AdCreate(**json_data)
        except ValidationError as e:
            return get_http_error(web.HTTPUnprocessableEntity, e.errors())

        ad.title = ad_data.title
        ad.content = ad_data.content
        ad.owner = ad_data.owner

        await self.request.session.commit()
        return web.json_response(ad.dict())

@routes.get("/ads")
async def get_all_ads(request):
    session = request.session
    result = await session.execute(select(Ad))
    ads = result.scalars().all()
    return web.json_response([ad.dict() for ad in ads])

app.add_routes(
    [
        web.post("/ads", AdView),
        web.get("/ads/{ad_id:[0-9]+}", AdView),
        web.delete("/ads/{ad_id:[0-9]+}", AdView),
        web.patch("/ads/{ad_id:[0-9]+}", AdView)
    ]
)


web.run_app(app, host='127.0.0.1', port=8080)