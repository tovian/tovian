@echo off
set PYTHONPATH=%PYTHONPATH%;%~dp0..\..

python update_version_info.py || goto :error

python setup.py py2exe || goto :error

goto :EOF


:error
echo Failed with error #%errorlevel%.
exit /b %errorlevel%
