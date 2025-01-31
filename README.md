# QuarrySaver
A python script to create a list of waypoints of immovable blocks where you want to build a quarry or world-eater. Made for 1.21.4 (checks trial chambers) but should work on lower versions as well.

# WARNING!
The current version (v1.1.0) only works in Linux, as it uses some memory optimisations that are only available there.  
Use [version v1.0.0](https://github.com/BigBeefyCow666/QuarrySaver/tree/old-v1.0.0) (About 3x slower and much more memory intensive) for Windows or MacOS. (I might make a better one for non-Linux one day)

# Prerequisites
1. Python 3 (ofc)
2. numpy python library (pip install numpy)
3. nbt python library (pip install nbt)

All other libraries should already be installed (I think, let me know if that isnt the case).

# How to use
Download the [python script](QuarrySaver.py) and install the prerequistes.

![2025-01-05_13 02 12](https://github.com/user-attachments/assets/5cc1d6a8-b7a8-483b-8d40-e52d30437d31)
Take a litematica area selection of the area you will build your quarry/world-eater.

![2025-01-05_13 02 26](https://github.com/user-attachments/assets/781528e5-336b-4c75-aadf-1e2287429b0f) 

Note down the smallest (most negative) x, y and z values of the schematic placement.
In this case the smallest x value is 208, y -51 and z 843.

![2025-01-05_13 06 02](https://github.com/user-attachments/assets/e2e1d250-a4a5-4120-8217-53f026d1cba9)
Now save the schematic and run the QuarrySaver.

The program will first ask for the litematica file, locate the schematic file you saved ({minecraft folder}/schematics).
Now enter the coordinates that you noted down from the origin of the schematic.
The program will then show you the blocks it will look for, by default these are all immovable blocks.
Then you can add/remove blocks from this list using the next prompts.
Next select what minimap mod you are using, VoxelMap (v) or Xaero's (x).
The program will now run.

When it is done finding blocks, it will ask you for a file to save the waypoints to, a .txt if using Xaero's, or a .points if using VoxelMap.
You can save this file anywhere and then copy the waypoints across, or select the waypoint file for the server/world (be warned this WILL ERASE the file entirely!)

![2025-01-05_14 24 29](https://github.com/user-attachments/assets/316e9111-cfc8-409f-b127-c6744486ee93)
Relog and the waypoints should now be in your world!

# Preformance
## Speed
Due to the enhancements in v1.1.0 (using shared memory and combining decoding and checking functions), I was easily able to run the 1 billion block file, analysing it in 90 seconds (I was getting that time on a quater billion block file just the other day)! It used 10GB of RAM while doing this (trust me compared to previous versions this is very good). So I'm gonna say it uses about 1GB of RAM per 100 million blocks in a schematic. (This is a rough estimate)

## Compared to previous versions
OK, so my goal was to make it run faster than JKM and SweetBaboos's version, so lets look at the numbers. These tests were made using the same litematica file, same settings and same machine:

QuarrySaver v1.1.0:
```
Read and analysed 286,858,440 blocks in 0:00:24.749412 (24.749 seconds) finding 5244 illegal blocks.
```
QuarrySaver v1.0.0:
```
Read and analysed 286,858,440 blocks in 0:01:10.415282 (70.415 seconds) finding 5244 illegal blocks.
```
JKM and SweetBaboo's:   
```
Total elapsed time: 278.3692 seconds
Load time: 220.3033 seconds
Process time: 28.3054 seconds
```
278.4 / 24.7 = 11.27 times faster than JKM and SweetBaboo's! So I'd say my project was a success!

# Credits
I got the idea to make this after seeing JKM and SweetBaboo's version they made and how slow it was, and wanted to improve the quality of life of building a quarry (and to prove that python can be fast if written right).  
Credit to the decoding algorithm for litematica files goes to the [litemapy library](https://pypi.org/project/litemapy/), which I just copied the source for decoding, de-bloated and made work in parallel.
