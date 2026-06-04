import asyncio, httpx, base64

async def test():
    headers = {"Content-Type": "application/json"}
    
    pdf_path = r"C:\Users\admin\Desktop\11\fuchuang1\jianli\27万本科Java~.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    print(f"PDF: {len(pdf_bytes)} bytes, base64: {len(b64)} chars")
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        try:
            print("Sending POST...")
            resp = await client.post(
                "https://mineru.net/api/v1/agent/parse/file",
                headers=headers,
                json={"file_name": "test.pdf", "language": "ch", "file_content": b64}
            )
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print(f"code={data.get('code')}, msg={data.get('msg')}")
            if data.get("code") == 0:
                task_id = data["data"]["task_id"]
                print(f"task_id: {task_id}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {str(e)[:200]}")

asyncio.run(test())