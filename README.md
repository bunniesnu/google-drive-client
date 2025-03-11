# Google Drive Image Iterator

A Python client for iterating through images stored in Google Drive folders using service account authentication.

## Requirements

This was tested on Python version 3.12.9, so other versions can cause errors.

Minimum Python version required for [google-api-python-client](https://github.com/googleapis/google-api-python-client) is >= 3.7

## Installation

First, clone this repository or just simply copy api.py.

Then, install the required dependencies:

```pip install -r requirements.txt```

or if you didn't clone (might occur version conflicts):

```pip install google-api-python-client```

## Usage

First, place your Google API service account credentials json file in your working directory. The file structure might be like this:

```
.
├── api.py
└── credentials.json
```

Then, initialize your client by:

```
from api import GoogleDriveClient

client = GoogleDriveClient("path/to/credentials.json")
```

Then, iter through images in your folder:

```
iter = client.iter_images("folder_id")
```

You can find the id from the url of the folder:

```https://drive.google.com/drive/u/2/folders/<folder-id>```

For example, if the link is ```https://drive.google.com/drive/u/2/folders/abcdefg```, then the folder id is ```abcdefg```.

Make sure your service account has access to Google Drive API, has a role more than or equal to 'Viewer', and the folder shared to the corresponding client email (found inside the service account json file).

## For Python beginners: Few examples

If you want to load pillow image (a.k.a PIL) from iter_images:

```
from io import BytesIO
from PIL import Image

for byte in client.iter_images("folder_id"):
    image = Image.open(BytesIO(byte))
    # Do something with the image
```

Or if you want to save the image to file:
```
for byte in client.iter_images("folder_id"):
    with open("file_name", "wb") as f:
        f.write(byte)