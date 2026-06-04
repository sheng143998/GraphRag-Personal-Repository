import asyncio, httpx, base64, io, zipfile

async def test():
    token = "pnxoq6d2gjqx2a4g8dyx"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    pdf_path = r"C:\Users\admin\Desktop\11\fuchuang1\jianli\27万本科Java~.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    print(f"PDF size: {len(pdf_bytes)} bytes")
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://mineru.net/api/v4/file-urls/batch", 
            headers=headers, json={"files": [{"name": "test.pdf"}]})
        data = resp.json()
        print(f"Step 1: code={data.get('code')}, msg={data.get('msg')}")
        
        if data.get("code") != 0:
            print("FAILED")
            return
        
        batch_id = data["data"]["batch_id"]
        upload_url = data["data"]["file_urls"][0]
        print(f"batch_id: {batch_id}")
        
        resp2 = await client.put(upload_url, content=pdf_bytes)
        print(f"Step 2 upload: {resp2.status_code}")
        
        await asyncio.sleep(3)
        poll_url = f"https://mineru.net/api/v4/extract/task/{batch_id}"
        for i in range(60):
            resp3 = await client.get(poll_url, headers=headers)
            poll = resp3.json()
            state = poll.get("data", {}).get("state", "unknown")
            print(f"Poll {i+1}: state={state}")
            if state == "done":
                zip_url = poll["data"].get("full_zip_url", "")
                print(f"DONE! zip_url={zip_url[:80]}")
                if zip_url:
                    zip_resp = await client.get(zip_url)
                    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
                        for name in zf.namelist():
                            if name.endswith(".md"):
                                md = zf.read(name).decode("utf-8", errors="replace")
                                print(f"Markdown: {len(md)} chars")
                                print(md[:800])
                                break
                return
            elif state == "failed":
                print(f"FAILED: {poll['data'].get('err_msg')}")
                return
            await asyncio.sleep(2)
        print("TIMEOUT")

asyncio.run(test())