from fastapi import FastAPI,WebSocket,WebSocketDisconnect,websockets,WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from services.auth_service.routes import auth_routes as auth_routerss
from study_rag_service.routes import study_routes


app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
    allow_credentials=True
)


app.include_router(auth_routerss.router,prefix="/auth",tags=["auth"])
app.include_router(study_routes.router, prefix="/teacher", tags=["Teacher"])
app.include_router(study_routes.router, prefix="/student", tags=["student_study"])


