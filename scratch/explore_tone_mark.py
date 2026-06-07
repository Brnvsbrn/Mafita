import os
import inspect
from dotenv import load_dotenv
from spitch import Spitch

load_dotenv()
api_key = os.getenv("SPITCH_API_KEY")
client = Spitch(api_key=api_key)

print("Signature of client.text.tone_mark:")
print(inspect.signature(client.text.tone_mark))

print("\nTesting client.text.tone_mark with raw Yoruba text:")
test_text = "Mo gbe owo lati PalmPay si Access Bank sugbon o kuna owo mi si ti lo"

try:
    # Let's inspect the method arguments or try calling it with standard parameters
    # Usually it takes text, language, or similar.
    # Let's try text=test_text first.
    result = client.text.tone_mark(
        language="yo",
        text=test_text
    )
    print("Success! Result type:", type(result))
    print("Result attributes:", dir(result))
    
    # Let's see what is inside the result
    if hasattr(result, "text"):
        print("Restored Text:", result.text)
    else:
        print("Result:", result)
        
except Exception as e:
    print("Error calling client.text.tone_mark:", e)
