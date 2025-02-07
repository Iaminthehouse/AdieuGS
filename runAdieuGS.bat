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

IF "%~2"=="" (
    SET input_dir=../../input
) ELSE (
    SET input_dir=%~2
)

IF "%~3"=="" (
    SET output_dir=../../output
) ELSE (
    SET output_dir=%~3
)

echo starting background removal...
cd ./ext/rmbg
@echo off
call myenv\Scripts\activate
REM rembg p -m birefnet-portrait %input_dir% %output_dir%
rembg p -m %model% %input_dir% %output_dir%/images
call myenv\Scripts\deactivate.bat
cd %myroot%
echo starting normals creation...
cd ./ext/normals
call myenv\Scripts\activate 
echo calling git with %output_dir%/images %output_dir%/normals
REM %myroot%/ext/normals/sapiens/lite/scripts/demo/torchscript/startnormalmap.bat %myroot% %output_dir%/images %output_dir%/normals
git bash %myroot%/ext/normals/sapiens/lite/scripts/demo/torchscript/startnormalmap.sh %myroot% %output_dir%/images %output_dir%/normals
call myenv\Scripts\deactivate.bat
echo cleaning directories...
cd %input_dir%
del /q *.txt
cd %output_dir%
del /q *.npy
echo files creation finished...
