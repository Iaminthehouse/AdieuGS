set myroot=%CD%
echo working directory is %myroot%
echo starting background removal...
cd ./ext/rmbg
@echo off
call myenv\Scripts\activate
rembg p -m birefnet-portrait ../../input ../../output/images
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
