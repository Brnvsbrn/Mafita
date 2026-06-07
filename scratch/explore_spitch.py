import spitch

print("Spitch package attributes:")
print(dir(spitch))

if hasattr(spitch, "Spitch"):
    client = spitch.Spitch(api_key="dummy")
    print("\nClient attributes:")
    print(dir(client))
    
    for attr in dir(client):
        if not attr.startswith("_"):
            obj = getattr(client, attr)
            print(f"\nclient.{attr} type: {type(obj)}")
            print(f"client.{attr} attributes: {dir(obj)}")
