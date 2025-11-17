@echo on
echo Setting up Visual Studio environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars32.bat"
echo.
echo Changing to project directory...
cd /d "C:\Projects\stock-system\trading-system\api\SAMPLES\VC++"
echo.
echo Building project...
msbuild WMCALOADER.vcxproj /p:Configuration=Release /p:Platform=Win32 /v:normal
echo.
echo Build completed with exit code: %ERRORLEVEL%
