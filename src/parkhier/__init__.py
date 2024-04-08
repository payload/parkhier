import httpx

DRESDEN_DE = "https://www.dresden.de/apps_ext/ParkplatzApp/index"

def hello() -> str:
    response = httpx.get(DRESDEN_DE)
    print(response.text)
    return "Hello from parkhier!"