import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

model_name = "models/gemini-2.5-flash"
print(f"Testing model: {model_name}")

try:
    resp = client.models.generate_content(
        model=model_name,
        contents="hello",
        config=types.GenerateContentConfig(max_output_tokens=1)
    )
    
    # Check all attributes of response
    print(f"\nResponse attributes: {[x for x in dir(resp) if not x.startswith('_')]}")
    
    # Check if there's a usage_metadata
    if hasattr(resp, 'usage_metadata'):
        print(f"\nUsage metadata: {resp.usage_metadata}")
    
    # Check if there's raw response with headers
    if hasattr(resp, "sdk_http_response") and resp.sdk_http_response:
        h = resp.sdk_http_response.headers or {}
        print(f"\nAll response headers ({len(h)} total):")
        for key in sorted(h.keys()):
            print(f"  {key}: {h[key]}")
        
        # Check if there's response body
        if hasattr(resp.sdk_http_response, 'body'):
            print(f"\nResponse body: {resp.sdk_http_response.body[:500] if hasattr(resp.sdk_http_response.body, '__getitem__') else resp.sdk_http_response.body}")
    
    # Try to get model info differently 
    print(f"\n--- Trying models.get() ---")
    try:
        model_info = client.models.get(model=model_name)
        print(f"Model info attributes: {[x for x in dir(model_info) if not x.startswith('_')]}")
        print(f"Model: {model_info}")
    except Exception as e2:
        print(f"Error: {e2}")
    
    print(f"\n--- Trying to list models with details ---")
    for m in client.models.list():
        if "gemini-2.5-flash" in m.name:
            print(f"Model: {m.name}")
            print(f"  supported_actions: {m.supported_actions}")
            print(f"  display_name: {getattr(m, 'display_name', 'N/A')}")
            print(f"  description: {getattr(m, 'description', 'N/A')[:200] if hasattr(m, 'description') else 'N/A'}")
            print(f"  All attrs: {[x for x in dir(m) if not x.startswith('_')]}")
            break

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")