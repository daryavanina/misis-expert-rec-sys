import requests

url = "https://api.apilayer.com/text_to_emotion"

payload = "She gasped in astonishment at the unexpected gift.".encode("utf-8")
headers= {
  "apikey": "WAzBy0DCGelQZtTrbGMywRcPOfMUabD3"
}

response = requests.request("POST", url, headers=headers, data = payload)

status_code = response.status_code
result = response.text
print(result)