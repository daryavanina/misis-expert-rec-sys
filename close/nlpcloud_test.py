import nlpcloud

client = nlpcloud.Client("distilbert-base-uncased-emotion", "283b0bcc0c4331cc566d6197e4875a2751aa9e5d")
# Returns a json object.
print(client.sentiment("She gasped in astonishment at the unexpected gift.", target="NLP Cloud"))

