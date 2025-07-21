"""Second Brain FastAPI application."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import close_db, init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE)
        if settings.LOG_FILE
        else logging.NullHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理."""
    logger.info("正在启动Second Brain后端服务...")

    # 启动时初始化数据库
    try:
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

    logger.info("Second Brain后端服务启动完成")
    yield

    # 关闭时清理资源
    logger.info("正在关闭Second Brain后端服务...")
    try:
        await close_db()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Second Brain - AI智能知识管理系统后端API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# 中间件配置 - 临时允许所有origins解决CORS问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有origins
    allow_credentials=False,  # 设为False以配合*
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 信任主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "43.160.192.140", "*.secondbrain.ai"],
    )


# @app.middleware("http")
# async def metrics_middleware(request: Request, call_next):
#     """指标收集中间件."""
#     if not settings.ENABLE_METRICS:
#         return await call_next(request)
#
#     # 开始计时
#     start_time = asyncio.get_event_loop().time()
#
#     # 处理请求
#     response = await call_next(request)
#
#     # 计算处理时间
#     process_time = asyncio.get_event_loop().time() - start_time
#
#     # 记录指标
#     REQUEST_COUNT.labels(
#         method=request.method, endpoint=request.url.path, status=response.status_code
#     ).inc()
#
#     REQUEST_DURATION.observe(process_time)
#
#     # 添加响应头
#     response.headers["X-Process-Time"] = str(process_time)
#
#     return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": asyncio.get_event_loop().time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors(),
            "status_code": 422,
            "timestamp": asyncio.get_event_loop().time(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器."""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "status_code": 500,
            "timestamp": asyncio.get_event_loop().time(),
            "path": request.url.path,
        },
    )


# 基础路由
@app.get("/")
async def root():
    """根路由."""
    return {
        "message": "Welcome to Second Brain API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查端点."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": asyncio.get_event_loop().time(),
    }


# @app.get("/metrics")
# async def metrics():
#     """Prometheus指标端点."""
#     if not settings.ENABLE_METRICS:
#         return JSONResponse(status_code=404, content={"detail": "Metrics not enabled"})
#
#     return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
