@echo off

echo To update Tovian, press any key to continue.
echo To cancel update, close this window.

pause

echo Downloading update. This can take time with slow internet connection!
tovian_cli.exe update win32_stable

echo Updating files...
xcopy data\update\* . /E /C /R /Y

echo Cleaning update files...
rmdir data\update /s /q

echo --------------------
echo UPDATE IS COMPLETED!
echo --------------------

pause