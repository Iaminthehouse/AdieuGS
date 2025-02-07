set myroot=%CD%
echo working directory is %myroot%

echo off
REM Dieses Skript ruft rembg p mit einem Modellnamen auf. 
REM Wird kein Modellname als Parameter übergeben, wird "birefnet-general" verwendet.

IF "%~1"=="" (
    SET model=birefnet-general
) ELSE (
    SET model=%~1
)

echo starting background removal...
cd ./ext/rmbg
@echo off
call myenv\Scripts\activate
REM rembg p -m birefnet-portrait ../../input ../../output/images
rembg p -m %model% ../../input ../../output/images
call myenv\Scripts\deactivate.bat
cd %myroot%
echo starting normals creation...
cd ./ext/normals
call myenv\Scripts\activate
git bash %myroot%/ext/normals/sapiens/lite/scripts/demo/torchscript/startnormalmap.sh %myroot%
call myenv\Scripts\deactivate.bat
echo cleaning directories...
cd %myroot%/input
del /q *.txt
cd %myroot%/output/normals
del /q *.npy
