import fastapi
from .service.data_source import router as ds_router

app = fastapi.FastAPI(title='Mindweaver')
app.include_router(ds_router)