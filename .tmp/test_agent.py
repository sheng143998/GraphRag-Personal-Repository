import asyncio, httpx

async def test():
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Agent API: submit URL parse task
        resp = await client.post(
            "https://mineru.net/api/v1/agent/parse/url",
            headers=headers,
            json={"url": "https://arxiv.org/pdf/1706.03762.pdf", "language": "en", "enable_table": True}
        )
        data = resp.json()
        print(f"Submit: code={data.get('code')}, msg={data.get('msg')}")
        
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
                print(f"DONE! md_url={md_url[:80]}")
                if md_url:
                    md_resp = await client.get(md_url)
                    print(f"Markdown: {len(md_resp.text)} chars")
                    print(md_resp.text[:800])
                return
            elif state == "failed":
                print(f"FAILED: {poll['data'].get('err_msg')}")
                return
        print("TIMEOUT")

asyncio.run(test())