@echo off
:loop 
@python "FULL_PATH_TO_PYTHON_FILE_HERE"
timeout /t 300
goto :loop 