#!/bin/bash

# List all items
curl -X GET http://localhost:8000/api/items

# Search items
curl -X GET "http://localhost:8000/api/items/search?name=Computer"