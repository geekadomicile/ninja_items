#!/bin/bash

# Test item creation and relationships
curl -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d '{"name":"Test Item","description":"Test Description"}'

# Test component history
curl -X GET http://localhost:8000/api/items/history