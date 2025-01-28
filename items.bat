@echo off
setlocal enabledelayedexpansion

echo === Creating Computer A ===
curl -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"Computer A\",\"description\":\"Main workstation\"}"

echo === Creating Computer B ===
curl -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"Computer B\",\"description\":\"Backup workstation\"}"

echo === List All Items ===
curl http://localhost:8000/api/items

pause