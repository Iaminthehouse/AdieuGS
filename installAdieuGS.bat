set myroot=%CD%
echo working directory is %myroot%
mkdir input
mkdir output\images
mkdir output\normals
mkdir ext\rmbg

REM Install rembg
echo Installing rembg...
cd ext\rmbg
python -m venv myenv
@echo off
call myenv\Scripts\activate
pip install rembg[gpu,cli]
call myenv\Scripts\deactivate.bat
cd %myroot%

REM Install sapiens
echo Installing sapiens...
mkdir ext\normals
cd ext/normals
python -m venv myenv
@echo off
call myenv\Scripts\activate
git clone https://github.com/facebookresearch/sapiens.git
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install opencv-python tqdm json-tricks
call myenv\Scripts\deactivate.bat

REM Install the model for normal creation
mkdir sapiens\lite\normal\checkpoints\sapiens_2b
cd sapiens\lite\normal\checkpoints\sapiens_2b
echo Installing normal model...
@echo off
curl -L --progress-bar -O "https://huggingface.co/facebook/sapiens-normal-2b-torchscript/resolve/main/sapiens_2b_normal_render_people_epoch_70_torchscript.pt2?download=true"
echo Download abgeschlossen!
call myenv\Scripts\deactivate.bat
cd %myroot%

REM manage scripts update
@echo off
copy ".\scripts\normalmap.py" ".\ext\normals\sapiens\lite\demo"
copy ".\scripts\startnormalmap.sh" ".\ext\normals\sapiens\lite\scripts\demo\torchscript"
echo files are moved successfully.

