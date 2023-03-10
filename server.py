from fastapi.logger import logger
import sys
import os
from fastapi import FastAPI

logger.info("Initializing FastAPI...")
app = FastAPI()
logger.info("FastAPI App Initialized.")
logger.debug(str(app))

"""
Database Model Load
"""
logger.info("Loading DB Models...")

from db.models import Series, Post, Tag

logger.info("DB Models Loaded.")


"""
FastAPI Initialization
"""
from fastapi import Depends, HTTPException, APIRouter


"""
Request & Response Model Section
"""
from pydantic_models import (
    UserLoginRequest,
    TokenRequest,
    TokenResponse,
    ResultBoolResponse,
    SeriesCreateRequest,
    SingleSeriesResponse,
    SeriesUpdateRequest,
    PostCreateRequest,
    TagCreateRequest,
    SingleTagResponse,
    SinglePostResponse,
    PostUpdateRequest, TagUpdateRequest,
    SeriesIdResponse,
    PostSearchResult,
    SeriesSearchResult,
    TagSearchResult, DeleteRequest,
)

logger.info("FastAPI Request & Response Initialized.")


"""
Security Initialization Section
"""
from secrets import token_hex
from datetime import timedelta, datetime

ADMIN_ID: str | None = os.environ.get("ADMIN_ID", None)
ADMIN_PW: str | None = os.environ.get("ADMIN_PW", None)

logger.info("Security Initialized.")
# logger.debug(f"ADMIN_ID {ADMIN_ID} | ADMIN_PW {ADMIN_PW}")  # Not recommended to uncomment this
if not (ADMIN_ID and ADMIN_PW):
    logger.warning("ADMIN_ID or ADMIN_PW not provided in environment variable.")
    sys.exit(1)


class AdminSession:
    def __init__(self):
        self.token: str = token_hex(50)
        self.expire: timedelta = timedelta(days=7)
        self.created: datetime = datetime.now()
        logger.info(f"AdminSession Created at {self.created}")

    async def is_expired(self) -> bool:
        if self.created + self.expire < datetime.now():
            return True
        return False

    async def refresh(self) -> None:
        self.token = token_hex(50)
        self.created = datetime.now()
        logger.info(f"AdminSession refreshed at {self.created}")

    async def serialize(self) -> TokenResponse:
        return TokenResponse(
            token=self.token
        )


ADMIN_SESSION: AdminSession | None = None


"""
Security Route Section
"""
from fastapi import Query

@app.post("/login", response_model=TokenResponse)
async def login(form_data: UserLoginRequest):
    global ADMIN_SESSION

    if not (form_data.username and form_data.password):
        raise HTTPException(status_code=400, detail={"error": "Login details not provided."})
    if form_data.username == ADMIN_ID and form_data.password == ADMIN_PW:
        if ADMIN_SESSION is None:
            ADMIN_SESSION = AdminSession()
        if await ADMIN_SESSION.is_expired():
            await ADMIN_SESSION.refresh()
        return await ADMIN_SESSION.serialize()
    raise HTTPException(status_code=401, detail={"error": "Invalid login details."})

@app.post("/validate")
async def validate(body: TokenRequest):
    global ADMIN_SESSION

    if ADMIN_SESSION is not None and body.token == ADMIN_SESSION.token and not await ADMIN_SESSION.is_expired():
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail={"error": "Invalid token."})

@app.post("/logout")
async def logout(body: TokenRequest):
    global ADMIN_SESSION

    if ADMIN_SESSION is not None and body.token == ADMIN_SESSION.token and not await ADMIN_SESSION.is_expired():
        ADMIN_SESSION = None
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail={"error": "Invalid token."})

logger.info("Security Route Ready.")


"""
Dependency Section
"""
from fastapi import Header

async def admin_session(token: str = Header(...)):
    global ADMIN_SESSION

    if ADMIN_SESSION is not None and token == ADMIN_SESSION.token and not await ADMIN_SESSION.is_expired():
        return ADMIN_SESSION
    raise HTTPException(status_code=401, detail={"error": "Invalid token."})

logger.info("Dependency Initialized.")

"""
Route Section
"""
"""
Admin Section
"""
from typing import List
from tortoise.functions import Count

admin = APIRouter(dependencies=[Depends(admin_session)])

@admin.get("/post", response_model=PostSearchResult)
async def get_posts(
        page: int = Query(1, alias="p", title="page"),
        query_title: str = Query(None, alias="qn", title="query title"),
        query_tags: list[int] = Query(None, alias="qt", title="query tags")):
    queryset = Post.all().distinct()
    if query_title is not None:
        queryset = queryset.filter(title__icontains=query_title)
    if query_tags is not None:
        queryset = queryset.filter(tags__id__in=query_tags).annotate(tag_count=Count('tags')).filter(tag_count__gte=len(query_tags))
    items = await queryset.order_by("-id").limit(10).offset((page - 1) * 10)
    max_page = await queryset.count() // 10 + 1
    return PostSearchResult(
        posts=items,
        max_page=max_page,
    )

@admin.post("/post", response_model=SinglePostResponse)
async def create_post(body: PostCreateRequest):
    post = await Post.create(
        title=body.title,
        content=body.content,
        description=body.description,
        series_id=body.series_id,
        thumbnail=body.thumbnail,
        hidden=body.hidden,
    )
    if body.tags:
        for tag in body.tags:
            await post.tags.add((await Tag.get(id=tag)))
    return await SinglePostResponse.from_tortoise_orm(post)

@admin.patch("/post", response_model=SinglePostResponse)
async def update_post(body: PostUpdateRequest):
    post = await Post.get_or_none(id=body.id)
    if post is None:
        raise HTTPException(status_code=404, detail={"error": "Post not found."})
    if body.title is not None:
        post.title = body.title
    if body.content is not None:
        post.content = body.content
    if body.description is not None:
        post.description = body.description
    if body.series_id is not None:
        post.series_id = body.series_id
    if body.thumbnail is not None:
        post.thumbnail = body.thumbnail
    if body.hidden is not None:
        post.hidden = body.hidden
    if body.tags is not None:
        await post.tags.clear()
        for tag in body.tags:
            await post.tags.add(await Tag.get(id=tag))
    await post.save()
    return await SinglePostResponse.from_tortoise_orm(post)

@admin.delete("/post")
async def delete_post(body: DeleteRequest):
    post = await Post.get_or_none(id=body.id)
    if post is None:
        raise HTTPException(status_code=404, detail={"error": "Post not found."})
    post.series = None
    await post.save()
    await post.tags.clear()
    await post.delete()
    return ResultBoolResponse(result=True)

@admin.get("/post/unique-title", response_model=ResultBoolResponse)
async def post_unique_title(query: str):
    if await Post.filter(title=query).exists():
        return ResultBoolResponse(result=False)
    return ResultBoolResponse(result=True)

@admin.get("/post/search-by-title", response_model=List[SinglePostResponse])
async def post_search_by_title(query: str):
    response = await \
        SinglePostResponse.from_queryset(Post.filter(title__icontains=query, series=None).order_by("-id"))
    return response

@admin.get("/tag", response_model=TagSearchResult)
async def get_tags(page: int = Query(1, alias="p", title="page"), query_name: str = Query(None, alias="qn", title="query name")):
    queryset = Tag.all()
    if query_name is not None:
        queryset = queryset.filter(name__icontains=query_name)
    items = await queryset.order_by("-id").limit(10).offset((page - 1) * 10)
    max_page = (await queryset.count()) // 10 + 1
    return TagSearchResult(
        tags=items,
        max_page=max_page,
    )

@admin.post("/tag", response_model=SingleTagResponse)
async def create_tag(body: TagCreateRequest):
    tag = await Tag.create(
        name=body.name,
    )
    return tag

@admin.patch("/tag", response_model=SingleTagResponse)
async def update_tag(body: TagUpdateRequest):
    tag = await Tag.get_or_none(id=body.id)
    if tag is None:
        raise HTTPException(status_code=404, detail={"error": "Tag not found."})
    if body.name is not None:
        tag.name = body.name
    await tag.save()
    return tag

@admin.delete("/tag", response_model=ResultBoolResponse)
async def delete_tag(body: DeleteRequest):
    tag = await Tag.get_or_none(id=body.id)
    if tag is None:
        raise HTTPException(status_code=404, detail={"error": "Tag not found."})
    await tag.posts.clear()
    await tag.series.clear()
    await tag.delete()
    return ResultBoolResponse(result=True)

@admin.get("/tag/unique-name", response_model=ResultBoolResponse)
async def tag_unique_name(query: str):
    if await Tag.filter(name=query).exists():
        return ResultBoolResponse(result=False)
    return ResultBoolResponse(result=True)

@admin.get("/series", response_model=SeriesSearchResult)
async def get_series(page: int = Query(1), query_name: str = Query(None, alias="qn", title="query name"), query_tags: list[int] = Query(None, alias="qt", title="query tags")):
    queryset = Series.all().distinct()
    if query_name is not None:
        queryset = queryset.filter(name__icontains=query_name)
    if query_tags is not None:
        queryset = queryset.filter(tags__id__in=query_tags).annotate(tag_count=Count('tags')).filter(tag_count__gte=len(query_tags))
    items = await queryset.order_by("-id").limit(10).offset((page - 1) * 10)
    max_page = (await queryset.count()) // 10 + 1
    return SeriesSearchResult(
        series=items,
        max_page=max_page,
    )

@admin.post("/series", response_model=SingleSeriesResponse)
async def create_series(body: SeriesCreateRequest):
    series = await Series.create(
        name=body.name,
        description=body.description,
        thumbnail=body.thumbnail
    )
    if body.posts:
        for post in body.posts:
            await Post.filter(id=post).update(series=series)
    if body.tags:
        for tag in body.tags:
            await series.tags.add((await Tag.get(id=tag)))
    return series

@admin.patch("/series", response_model=SingleSeriesResponse)
async def update_series(body: SeriesUpdateRequest):
    series = await Series.get_or_none(id=body.id)
    if series is None:
        raise HTTPException(status_code=404, detail={"error": "Series not found."})
    if body.name is not None:
        series.name = body.name
    if body.description is not None:
        series.description = body.description
    if body.thumbnail is not None:
        series.thumbnail = body.thumbnail
    if body.posts is not None:
        await Post.filter(series_id=series.id).update(series_id=None)
        for post in body.posts:
            await Post.filter(id=post).update(series=series)
    if body.tags is not None:
        await series.tags.clear()
        for tag in body.tags:
            await series.tags.add(await Tag.get(id=tag))
    await series.save()
    return series

@admin.delete("/series", response_model=ResultBoolResponse)
async def delete_series(body: DeleteRequest):
    series = await Series.get_or_none(id=body.id)
    if series is None:
        raise HTTPException(status_code=404, detail={"error": "Series not found."})
    await Post.filter(series_id=series.id).update(series_id=None)
    await series.tags.clear()
    await series.delete()
    return ResultBoolResponse(result=True)

@admin.get("/series/unique-name", response_model=ResultBoolResponse)
async def series_unique_name(query: str):
    if await Series.filter(name=query).exists():
        return ResultBoolResponse(result=False)
    return ResultBoolResponse(result=True)

@admin.get("/series/search-by-name", response_model=List[SingleSeriesResponse])
async def series_search_by_name(query: str):
    response = await \
        SingleSeriesResponse.from_queryset(Series.filter(name__icontains=query).order_by("-id"))
    return response

logger.info("Admin Route Ready.")
"""
General Section
"""
general = APIRouter()

@general.get("/post", response_model=PostSearchResult)
async def get_posts(
        page: int = Query(1, alias="p", title="page"),
        query_title: str = Query(None, alias="qn", title="query title"),
        query_tags: list[int] = Query(None, alias="qt", title="query tags")):
    queryset = Post.filter(series=None, hidden=False).distinct()
    if query_title is not None:
        queryset = queryset.filter(title__icontains=query_title)
    if query_tags is not None:
        queryset = queryset.filter(tags__id__in=query_tags).annotate(tag_count=Count('tags')).filter(tag_count__gte=len(query_tags))
    items = await queryset.order_by("-id").limit(10).offset((page - 1) * 10)
    max_page = await queryset.count() // 10 + 1
    return PostSearchResult(
        posts=items,
        max_page=max_page,
    )

@general.get("/post-ids", response_model=List[int])
async def get_posts_ids():
    return await Post.filter(hidden=False).values_list("id", flat=True)

@general.get("/post/{post_id}", response_model=SinglePostResponse)
async def get_single_post(post_id: int):
    post = await Post.get_or_none(id=post_id)
    if post is None:
        raise HTTPException(status_code=404, detail={"error": "Post not found."})
    return await SinglePostResponse.from_tortoise_orm(post)

@general.get("/post/{post_id}/get-tags", response_model=List[int])
async def get_post_tags(post_id: int):
    post = await Post.get_or_none(id=post_id)
    await post.fetch_related("tags")
    return [tag.id for tag in post.tags]

@general.get("/post/{post_id}/get-series", response_model=SeriesIdResponse)
async def get_post_series(post_id: int):
    post = await Post.get_or_none(id=post_id)
    if post is None:
        raise HTTPException(status_code=404, detail={"error": "Post not found."})
    await post.fetch_related("series")
    if post.series is None:
        return SeriesIdResponse(id=None)
    return SeriesIdResponse(id=post.series.id)

@general.get("/series", response_model=SeriesSearchResult)
async def get_series(page: int = Query(1), query_name: str = Query(None, alias="qn", title="query name"), query_tags: list[int] = Query(None, alias="qt", title="query tags")):
    queryset = Series.filter(hidden=False).distinct()
    if query_name is not None:
        queryset = queryset.filter(name__icontains=query_name)
    if query_tags is not None:
        queryset = queryset.filter(tags__id__in=query_tags).annotate(tag_count=Count('tags')).filter(tag_count__gte=len(query_tags))
    items = await queryset.order_by("-id").limit(10).offset((page - 1) * 10)
    max_page = (await queryset.count()) // 10 + 1
    return SeriesSearchResult(
        series=items,
        max_page=max_page,
    )

@general.get("/series-ids", response_model=List[int])
async def get_series_ids():
    return await Series.filter(hidden=False).values_list("id", flat=True)

@general.get("/series/{series_id}", response_model=SingleSeriesResponse)
async def get_single_series(series_id: int):
    series = await Series.get_or_none(id=series_id)
    if series is None:
        raise HTTPException(status_code=404, detail={"error": "Series not found."})
    return await SingleSeriesResponse.from_tortoise_orm(series)

@general.get("/series/{series_id}/get-posts", response_model=List[int])
async def get_series_posts(series_id: int):
    series = await Series.get_or_none(id=series_id)
    await series.fetch_related("posts")
    return [post.id for post in series.posts if not post.hidden]

@general.get("/series/{series_id}/get-tags", response_model=List[int])
async def get_series_tags(series_id: int):
    series = await Series.get_or_none(id=series_id)
    await series.fetch_related("tags")
    return [tag.id for tag in series.tags]

@general.get("/tag/search-by-name", response_model=List[SingleTagResponse])
async def tag_search_by_name(query: str):
    response = await \
        SingleTagResponse.from_queryset(Tag.filter(name__icontains=query).order_by("-id"))
    return response

@general.get("/tag/{tag_id}", response_model=SingleTagResponse)
async def get_single_tag(tag_id: int):
    tag = await Tag.get_or_none(id=tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail={"error": "Tag not found."})
    return await SingleTagResponse.from_tortoise_orm(tag)


logger.info("General Route Ready.")
"""
Add Route
"""

app.include_router(admin, prefix="/admin")
app.include_router(general, prefix="/api")
logger.info("Router Added.")

"""
Database Initialization
"""
logger.info("Initializing database...")


"""
Database Engine Section
"""
from tortoise.contrib.fastapi import register_tortoise

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["db.models"]},
    generate_schemas=True,  # disable on production | enable on development
    add_exception_handlers=True,
)


logger.info("Database engine initialized.")