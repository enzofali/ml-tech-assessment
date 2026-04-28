import fastapi
from app.api import routes

app = fastapi.FastAPI(title="Transcript Analyzer")
app.include_router(routes.router)
