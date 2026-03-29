from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import uvicorn
import sys

app = FastAPI(title="Leptixx Core")

class CheckRequest(BaseModel):
    statement: str

@app.post("/api/v1/check")
async def verify_statement(request: CheckRequest):
    # ВНИМАНИЕ: Проверь имя модели в команде 'ollama list'
    # Если там просто 'qwen-local', то пиши БЕЗ ':latest'
    model_name = "qwen-local" 
    
    payload = {
        "model": model_name,
        "prompt": f"Проверь факт: {request.statement}",
        "stream": False
    }

    # Используем AsyncClient с отключенными системными прокси
    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            print(f"--> Отправка запроса в Ollama (модель: {model_name})...")
            
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json=payload,
                timeout=60.0 # Даем больше времени на "разогрев"
            )
            
            # Если Ollama вернет ошибку (например, 503 или 404), мы увидим это здесь
            if response.status_code != 200:
                print(f"!!! Ollama ответила ошибкой: {response.status_code}")
                print(f"Текст ошибки: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Ollama error: {response.text}")

            result = response.json()
            return {"status": "success", "ai_response": result["response"]}

        except httpx.ConnectError:
            print("!!! Ошибка: Не удалось подключиться к Ollama. Проверь, запущен ли сервер!")
            raise HTTPException(status_code=503, detail="Ollama не запущена")
        except Exception as e:
            print(f"!!! Непредвиденная ошибка: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)