# AdieuGS
Using Blender I wanted to find an alternative to the greenscreen workflow for inserting 2D videos in 3D environment.   
This workflow removes the background from a image sequence and creates the related normal maps to enhance the lighting.  

__Installation (Windows only, GPU necessary)__  
As prerequisites, you should install both Python and Git Bash before proceeding.
- Create a working directory  
- Start a `cmd` 
- Go with `cd` to the working directory  
- Enter the following command `git clone https://github.com/fransoavirtuality/AdieuGS.git`
- Enter in the cmd windows`cd adieuGS`  
- After the repository has been copied call in the cmd windows `./installAdieuGS.bat`
- This will take a while, go drink a coffee or make some exercises or what you want


__startet the removal of the background& the creation of normal maps__  
- start the startUI.bat file. An application will appear  
![image](https://github.com/user-attachments/assets/41819558-6faa-46f3-b2d0-bd6124247bf6)  

- You have to select the model in the list box you want to use
- I recommand to test the model before. By clicking on the button you will be redirected to the demo page where you can test the differentsm models  
  ![image](https://github.com/user-attachments/assets/ad7cc1b3-d5e7-4e4f-b9af-b9df908d087f)  
- Then you have to select the input directory where the images to be proceesed are saved and select one output directory where the results (images without background & created normal maps) will be saved. Click on run to start the process.    
  ![image](https://github.com/user-attachments/assets/18e56c2c-fe57-4941-a3c1-9a8c70252494)

- The process will start the output og the process will be displayed. Some warnings may be displayed. For creating the normals a new window will open. Don't worry everything is ok  
![image](https://github.com/user-attachments/assets/35ffc577-a56d-4a94-920d-7bdd283d0bf8)  
  
- After clicking on the alert saying the process is finished, the output directory will open in the windows explorer.
__YOU ARE DONE!!!__     
