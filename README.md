# AdieuGS
using Blender I wanted to find an alternative to the greenscreen workflow for inserting 2D videos in 3 environment.   
This workflow removes the background from a image sequence and create the related normal map.  

__Installation (Windows only, GPU necessary)__    
- Create a working directory  
- Start a `cmd` 
- Go with `cd` to the working directory  
- Enter the following command `git clone https://github.com/fransoavirtuality/AdieuGS.git`
-  Enter in the cmd windows`cd adieuGS`  
- After the repository has been copied call in the cmd windows `./installAdieuGS.bat`
- This will take a while, go drink a coffee or make some exercises or what you want


__startet the removal of the background& the creation of normal maps__  
- save your image sequence in the `./input` directory
- Start a `cmd` 
- Go with `cd` to the working directory  
- Call in the cmd windows `./runAdieuGS.bat`
- Some errors may occurs
- After the batch is finished check the directories *output/images* & *output/normals*. 
