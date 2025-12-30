import json

# Re-assembling the private key
# The user provided key has \n literals.
lines = [
    "-----BEGIN PRIVATE KEY-----",
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQD3wfIxi2AuhyUY",
    "mW/6ZLd7tsr+VSPU4PkfLsihlNwuCHNJiWwqj8F5cREj9CgV2FXvj4J/4LNUWJlG",
    "yp/ani7gBcehIVY38/XPcGB12z10sPy656u7AFF4EHuFB+PEcAPP5onnffVE6we7",
    "mT7BwZrO6fgRms8ELaATyN96wHRHxEb3HY5nfXjWIXLEbp7PWMSTXNp0/6z0Ard1",
    "hize8Gx99MAIkXShDHTXl14GwSCELE3SMp1gITtQkqFPNmFFtOn64lcr917o9sqn",
    "fUwziTkaQ0b/R1T8lNkk8oAZq66aoVrNQtdG9p4VtxcmqAzYDSwQj5P2gQd4+a2F",
    "aAwU2eGNAgMBAAECggEAIuoCauf0vGnQGPjadmNGFhmK3q951rCDetj5bgfPxW7s",
    "bDMA+rh6b9Y2r6XjFjz/0zwajFHKg7reksLQJxs+iNRXrwXHJChtffecqE8miHC+",
    "lMo8AaTIVk6gUX1spAyTBPO8gFJYQ4eJde7hEKXrXnhLPJPf03togRFAKQjA+jHQ",
    "QMGWxFIZjz7u2X+kbEyUalwpYPrqtXxYJ6cHrAWKmKmMbch4xWTIB+wihl1gey3e",
    "f+xNJpGpd/dUw/Pl+h1QxXnlVdQrx77+QhgIVOT2T0MqDi+5Lu24QamV+fdomxSf",
    "Go/nhz1a2dtFmfXvjB6sWC1C5EWJmqQvrZ7hatUccQKBgQD9dwIxncG7iJe3QdfG",
    "vq51WfSDg4R+VdiwCST65g4HtdE87DwsBT+IZH9352QZFOQ1dtAY4Qk5EQ0flAmB",
    "UIs/76fnwr0UWB5Uyi/CZve8qr1rKC6ZdrHTTIlUE6poN6wgbDin6TBbcePI73B3",
    "GmDMeqvZRA7hrVxTI0SbfXF1yQKBgQD6PFL68SdVpserD4qNgJTHlRYhxilu4yfV",
    "1XxIGsBPSzfsvTQvfCTPKJ8PEEz/b6j0ZayUvlOI2UHhKQWLGF8t3jGjvRBkCr8n",
    "GSBmVaGZXkEtAYbgyYKjZ3WyeUAcuZoDXYh4inJy8tJPDf9s/gRlfmwiGjNW7C00",
    "22TlwRi/pQKBgEYuB3t5dMTaIzfokThEX8W6bItlhO/+EQtc3NJjlIrp+s9lkZuW",
    "sGqxeOHYPcz8DdwH08KvvIACiqGtuZwGkyfW0aTINNZHN86+VM7896dTlzLuY0i2",
    "prIcxQF0mIBWueAYVu+XD36iYDGoqnkv4pF7fc2gnIY8HA4g+8QZzaqRAoGBAJCK",
    "DahTaVQJDOYbCP3pGocZ73m8u6wIW7chJDOF+DUVDo2ZUC5pd92M6itKUB9vgNkC",
    "bahRM3ElhO8owcHxZvDYmjWo/HG832MXGWbi6X/sOJtleWIYI3R9Sze237h34KU2",
    "/qAZ4DfTWHU/cZ2kMCfr2UvtdGAt9YLFg0dOvRvdAoGAXkrlsKwG/qzEqvvod/ME",
    "RObl7A0GV/4fVZ8zq8mpmhjv8NApamCvy9/UNFXCa0UJ1EOh6bQlHan+mHpOeC67",
    "LJ+O6Ns3/BoW0QpW/zX3Tv1BsgI/TPw2HFod+zxupDhnWU0OpBj2ZcNNOXlKwFwC",
    "CPlWkCKR/FQC+O8LsIG89EM=",
    "-----END PRIVATE KEY-----"
]

# Google requires \n literals in the JSON string
private_key = "\n".join(lines)

data = {
  "type": "service_account",
  "project_id": "seo-orchestrador",
  "private_key_id": "2f28535072906358d9949446fa169847b3a7df0b",
  "private_key": private_key,
  "client_email": "seo-robo@seo-orchestrador.iam.gserviceaccount.com",
  "client_id": "113774259759820785016",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seo-robo%40seo-orchestrador.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

with open("config/service_account.json", "w") as f:
    json.dump(data, f, indent=2)
    print("Fixed service_account.json")
