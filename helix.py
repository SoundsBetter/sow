import requests
import json

API_KEY = "a5b5b179-92f9-42bc-8910-6cfb0f595d61"
URL = f"https://api.helius.xyz/v0/transactions?api-key={API_KEY}"

payload = {
    "transactions": [
        "5qU4y4zLWiV5XDt2JW1e1A46cdmwgurJ5Vf9os5QdNBrZKktQ8cb7pa8r2jTyAoGvFUUcpos7uvJoyDHf63aYGoN",
        "22FxmMr6DopEkctyG72wGnAPyDw3d5kPg2avM8aqDBkzut4YosheDXeU2QQsD2pXsR2idskTCaeaVMFGgkHRAkkS"
    ]
}
headers = {
    "Content-Type": "application/json"
}

resp = requests.post(URL, headers=headers, data=json.dumps(payload))
print("Status code:", resp.status_code)
print("Response JSON:", resp.json())
