import asyncio
import random
import string
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import json
import time
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# 加载环境变量
load_dotenv()


app = FastAPI()
MAX_RETRIES = 3
RETRY_DELAY = 1
API_KEY = os.getenv("API_KEY")

security = HTTPBearer()


# 定义模型返回的结构
class Model(BaseModel):
    id: str
    object: str
    created: int
    owned_by: str


class ModelList(BaseModel):
    data: list[Model]
    object: str


def get_random_string(length):
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


async def notforward_request(access_token: str, stream: bool, json_data, headers):
    model = json_data.get("model", "gpt-3.5-turbo")

    retries = 0
    while retries < MAX_RETRIES:
        try:
            if stream:

                async def generate():
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(999, read=250),
                        follow_redirects=True,
                    ) as client:
                        async with client.stream(
                            "POST",
                            "https://api.deepinfra.com/v1/openai/chat/completions",
                            headers=headers,
                            json=json_data,
                        ) as resp:
                            if resp.status_code != 200:
                                raise HTTPException(
                                    status_code=429,
                                    detail=f"上游API返回 {resp.status_code}",
                                )
                            async for line in resp.aiter_lines():
                                if line:
                                    yield (line + "\n\n").encode("utf-8")
                                if line == "data: [DONE]":
                                    break

                return generate()
            else:
                # 非流式响应处理
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(999, read=250),
                    follow_redirects=True,
                ) as client:
                    resp = await client.post(
                        "https://api.deepinfra.com/v1/openai/chat/completions",
                        headers=headers,
                        json=json_data,
                    )
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=429, detail=f"上游API返回 {resp.status_code}"
                        )
                    resp_data = resp.json()

                    # 错误处理
                    if not resp_data["choices"][0]["message"]["content"]:
                        raise HTTPException(status_code=500, detail="API返回无效响应")

                    # 数据清理
                    for choice in resp_data["choices"]:
                        choice.pop("content_filter_results", None)
                        choice["message"] = {
                            k: choice["message"][k] for k in ["role", "content"]
                        }

                    resp_data["choices"] = [
                        {k: c[k] for k in ["index", "message", "finish_reason"]}
                        for c in resp_data["choices"]
                    ]

                    # 构建新响应
                    return {
                        "id": resp_data["id"],
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": resp_data["choices"],
                        "usage": {
                            k: resp_data["usage"][k]
                            for k in [
                                "prompt_tokens",
                                "completion_tokens",
                                "total_tokens",
                            ]
                        },
                        "system_fingerprint": "fp_a24b4d720c",
                    }

            # 成功则退出重试循环
            break

        except HTTPException as e:
            retries += 1
            if retries < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise e
        except (httpx.ReadTimeout, json.JSONDecodeError):
            retries += 1
            if retries >= MAX_RETRIES:
                return JSONResponse(
                    status_code=500, content={"message": "多次重试后请求失败。"}
                )

            await asyncio.sleep(RETRY_DELAY)


@app.get("/v1/models", response_model=ModelList)
async def get_models():
    models = [
        {
            "id": "meta-llama/Meta-Llama-3.1-405B-Instruct",
            "object": "model",
            "created": 581983200,
            "owned_by": "system",
        },
        {
            "id": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "object": "model",
            "created": 581983200,
            "owned_by": "system",
        },
    ]
    return ModelList(data=models, object="list")


@app.post("/v1/chat/completions")
async def proxy(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """API代理入口"""
    # 校验API Key
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    json_data = await request.json()

    try:
        access_token = "1"

        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,zh-HK;q=0.6",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://deepinfra.com",
            "Referer": "https://deepinfra.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "X-Deepinfra-Source": "web-page",
            "accept": "text/event-stream",
            "content-type": "application/json",
        }
        stream = json_data.get("stream", False)

        resp = await notforward_request(access_token, stream, json_data, headers)

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"message": str(e.detail)}
        )

    return (
        StreamingResponse(resp, media_type="application/json")
        if stream
        else JSONResponse(resp)
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9999)
