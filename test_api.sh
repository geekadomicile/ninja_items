#!/bin/bash

echo "=== Creating Computer A ==="
COMP_A_ID=$(curl -s -X POST http://localhost:8000/api/items \
    -H "Content-Type: application/json" \
    -d '{"name":"Computer A","description":"Main workstation"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Computer A with ID: $COMP_A_ID"
curl -s -X GET "http://localhost:8000/api/items/$COMP_A_ID" | python3 -m json.tool
echo

echo "=== Creating Computer B ==="
COMP_B_ID=$(curl -s -X POST http://localhost:8000/api/items \
    -H "Content-Type: application/json" \
    -d '{"name":"Computer B","description":"Backup machine"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Computer B with ID: $COMP_B_ID"
curl -s -X GET "http://localhost:8000/api/items/$COMP_B_ID" | python3 -m json.tool
echo

echo "=== Creating GPU ==="
GPU_ID=$(curl -s -X POST http://localhost:8000/api/items \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"GPU\",\"description\":\"RTX 4090\",\"parent_id\":$COMP_A_ID}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created GPU with ID: $GPU_ID"
curl -s -X GET "http://localhost:8000/api/items/$GPU_ID" | python3 -m json.tool
echo

echo "=== Moving GPU ==="
curl -s -X PUT "http://localhost:8000/api/items/$GPU_ID/parent?new_parent_id=$COMP_B_ID" | python3 -m json.tool
echo

echo "=== Checking Hierarchy ==="
echo "Computer A children:"
curl -s "http://localhost:8000/api/items/$COMP_A_ID" | python3 -m json.tool
echo

echo "Computer B children:"
curl -s "http://localhost:8000/api/items/$COMP_B_ID" | python3 -m json.tool
echo

echo "=== Final Check ==="
curl -s "http://localhost:8000/api/items/$GPU_ID" | python3 -m json.tool
echo
