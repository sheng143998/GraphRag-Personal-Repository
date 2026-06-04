import asyncio, httpx, base64

async def test():
    headers = {"Content-Type": "application/json"}
    
    pdf_path = r"C:\Users\admin\Desktop\11\fuchuang1\jianli\27万本科Java~.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    print(f"PDF: {len(pdf_bytes)} bytes, base64: {len(b64)} chars")
    
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://mineru.net/api/v1/agent/parse/file",
            headers=headers,
            json={"file_name": "test.pdf", "language": "ch", "enable_table": True, "file_content": b64}
        )
        data = resp.json()
        print(f"Submit: code={data.get('code')}, msg={data.get('msg')}")
        print(f"Full response: {data}")
        
        if data.get("code") != 0:
            print("FAILED")
            return
        
        task_id = data["data"]["task_id"]
        print(f"task_id: {task_id}")
        
        for i in range(60):
            await asyncio.sleep(2)
            resp2 = await client.get(f"https://mineru.net/api/v1/agent/parse/{task_id}", headers=headers)
            poll = resp2.json()
            state = poll.get("data", {}).get("state", "unknown")
            print(f"Poll {i+1}: state={state}")
            if state == "done":
                md_url = poll["data"].get("markdown_url") or poll["data"].get("full_md_url", "")
                print(f"DONE! md_url={md_url[:100]}")
                if md_url:
                    md_resp = await client.get(md_url)
                    text = md_resp.text
                    print(f"Markdown: {len(text)} chars")
                    # Print first 1000 chars, replacing non-ASCII for console
                    safe = text[:1000].encode('ascii', errors='replace').decode()
                    print(safe)
                return
            elif state == "failed":
                print(f"FAILED: {poll['data'].get('err_msg')}")
                return
        print("TIMEOUT")

asyncio.run(test())