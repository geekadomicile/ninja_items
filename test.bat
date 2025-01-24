@echo off
setlocal enabledelayedexpansion

echo === Creating Gaming Computer ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"Gaming PC\",\"description\":\"High-end gaming rig\"}" ^| findstr "\"id\""') do (
    set "computer_id=%%~a"
)
set "computer_id=!computer_id: =!"
echo Created Gaming PC with ID: !computer_id!
echo Debug - Computer ID value: [!computer_id!
echo === Adding CPU ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"CPU\",\"description\":\"Intel i9-13900K\",\"parent_id\":!computer_id!}" ^| findstr "\"id\""') do (
    set "cpu_id=%%~a"
)
echo Added CPU with ID:!cpu_id!

echo === Adding RAM ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"RAM\",\"description\":\"64GB DDR5\",\"parent_id\":!computer_id!}" ^| findstr "\"id\""') do (
    set "ram_id=%%~a"
)
echo Added RAM with ID: !ram_id!

echo === Adding SSD ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/api/items -H "Content-Type: application/json" -d "{\"name\":\"SSD\",\"description\":\"2TB NVMe\",\"parent_id\":!computer_id!}" ^| findstr "\"id\""') do (
    set "ssd_id=%%~a"
)
echo Added SSD with ID:!ssd_id!

echo === Checking Complete Computer Setup ===
curl -s -X GET http://localhost:8000/api/items/!computer_id! -H "Content-Type: application/json" | python -m json.tool
echo Debug - Computer ID value: [!computer_id!]

echo.

pause
