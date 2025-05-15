from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.line.client import setup_line_client
from src.line.handlers import setup_line_handlers
from src.services.agent_service import setup_agent_runner


app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各モジュールの初期化
line_bot_api, handler = setup_line_client()
setup_line_handlers(app, line_bot_api, handler)
setup_agent_runner()


# ヘルスチェック用
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
