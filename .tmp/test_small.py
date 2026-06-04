import asyncio, httpx, base64

async def test():
    headers = {"Content-Type": "application/json"}
    
    # Use a small test - just a few bytes
    tiny = b"%PDF-1.4 test"
    b64 = base64.b64encode(tiny).decode()
    
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                "https://mineru.net/api/v1/agent/parse/file",
                headers=headers,
                json={"file_name": "test.pdf", "language": "ch", "file_content": b64}
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

asyncio.run(test())