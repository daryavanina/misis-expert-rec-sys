import asyncio
from llm_handler import get_gpt4o_response

async def test():
    resp = await get_gpt4o_response("Explain why people feel fear.")
    print(resp)

asyncio.run(test())
   
    
    