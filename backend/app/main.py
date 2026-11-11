import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.mqtt_client import mqtt_manager
from app.services.camera_stream import camera_manager
from app.routers import stream, incidents, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Database...")
    Base.metadata.create_all(bind=engine)

    logger.info("Starting MQTT Manager...")
    mqtt_manager.start()

    logger.info("Starting Video Camera Grabber Thread...")
    camera_manager.start()

    yield

    # Shutdown
    logger.info("Stopping Video Camera Grabber...")
    camera_manager.stop()

    logger.info("Stopping MQTT Manager...")
    mqtt_manager.stop()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware for React Vite Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(stream.router)
app.include_router(incidents.router)
app.include_router(system.router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": settings.APP_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

