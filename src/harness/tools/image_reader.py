from harness.core.result import ToolResult


def image_read(path: str, question: str = "Describe this image in detail") -> ToolResult:
    """
    Read an image and return a text description.
    Uses Qwen-VL API via httpx. Requires QWEN_VL_API_KEY in environment.
    This is a tool wrapper — the underlying API is a separate service.
    """
    import os
    import httpx
    import base64

    api_key = os.getenv("QWEN_VL_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return ToolResult(ok=False, output="",
                          error="Image reading requires QWEN_VL_API_KEY or DASHSCOPE_API_KEY in .env")

    try:
        with open(path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Qwen-VL via DashScope API
        response = httpx.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-vl-plus",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/jpeg;base64,{image_b64}"},
                                {"text": question},
                            ],
                        }
                    ]
                },
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            text = data.get("output", {}).get("text", "No description returned")
            return ToolResult(ok=True, output=text)
        else:
            return ToolResult(ok=False, output="",
                              error=f"Qwen-VL API error: {response.status_code} {response.text[:200]}")

    except FileNotFoundError:
        return ToolResult(ok=False, output="", error=f"Image file not found: {path}")
    except Exception as e:
        return ToolResult(ok=False, output="", error=f"Image reading failed: {str(e)}")