import asyncio, httpx, base64

pdf_path = r"C:\Users\admin\Desktop\11\fuchuang1\jianli\27万本科Java~.pdf"
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()
b64 = base64.b64encode(pdf_bytes).decode()
print(f"PDF: {len(pdf_bytes)} bytes")

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("https://mineru.net/api/v1/agent/parse/file",
            json={"file_name": "test.pdf", "language": "ch", "enable_table": True},
            headers={"Content-Type": "application/json"})
        data = resp.json()
        print(f"Step1: code={data.get('code')}, msg={data.get('msg')}")
        if data.get("code") != 0:
            return
        
        task_id = data["data"]["task_id"]
        file_url = data["data"]["file_url"]
        print(f"task_id={task_id}")
        
        resp2 = await client.put(file_url, content=pdf_bytes)
        print(f"Step2 PUT: {resp2.status_code}")
        
        for i in range(60):
            await asyncio.sleep(2)
            resp3 = await client.get(f"https://mineru.net/api/v1/agent/parse/{task_id}")
            poll = resp3.json()
            state = poll["data"]["state"]
            print(f"Poll {i+1}: {state}")
            if state == "done":
                md_url = poll["data"].get("markdown_url", "")
                if md_url:
                    md = (await client.get(md_url)).text
                    print(f"SUCCESS! Markdown: {len(md)} chars")
                    safe = md[:500].encode("ascii", errors="replace").decode()
                    print(safe)
                return
            elif state == "failed":
                print(f"FAILED: {poll['data'].get('err_msg')}")
                return
        print("TIMEOUT")

asyncio.run(test())