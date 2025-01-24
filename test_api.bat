@echo off
setlocal enabledelayedexpansion

echo === Creating Computer A ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/ninja_items/api/items -H "Content-Type: application/json" -d "{\"name\":\"Computer A\",\"description\":\"Main workstation\"}" ^| findstr "\"id\""') do (
    set "comp_a_id=%%~a"
)
echo Created Computer A with ID: !comp_a_id!
curl -s -X GET "http://localhost:8000/ninja_items/api/items/!comp_a_id!" | python -m json.tool
echo.

echo === Creating Computer B ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/ninja_items/api/items -H "Content-Type: application/json" -d "{\"name\":\"Computer B\",\"description\":\"Backup machine\"}" ^| findstr "\"id\""') do (
    set "comp_b_id=%%~a"
)
echo Created Computer B with ID: !comp_b_id!
curl -s -X GET "http://localhost:8000/api/items/!comp_b_id!" | python -m json.tool
echo.

echo === Creating GPU ===
for /f "tokens=2 delims=:," %%a in ('curl -s -X POST http://localhost:8000/ninja_items/api/items -H "Content-Type: application/json" -d "{\"name\":\"GPU\",\"description\":\"RTX 4090\",\"parent_id\":!comp_a_id!}" ^| findstr "\"id\""') do (
    set "gpu_id=%%~a"
)
echo Created GPU with ID: !gpu_id!
curl -s -X GET "http://localhost:8000/api/items/!gpu_id!" | python -m json.tool
echo.

echo === Moving GPU ===
curl -s -X PUT "http://localhost:8000/ninja_items/api/items/!gpu_id!/parent?new_parent_id=!comp_b_id!" | python -m json.tool
echo.

echo === Checking Hierarchy ===
echo Computer A children:
curl -s "http://localhost:8000/api/items/!comp_a_id!" | python -m json.tool
echo.

echo Computer B children:
curl -s "http://localhost:8000/api/items/!comp_b_id!" | python -m json.tool
echo.

echo === Final Check ===
curl -s "http://localhost:8000/api/items/!gpu_id!" | python -m json.tool
echo.

pause