from nbt import nbt
import numpy as np
import math
import time
import tkinter as tk
from tkinter import filedialog
from datetime import timedelta
import multiprocessing




def init():
    global workers, minimap, illegalPalette, origin, volume, sx,sy,sz, region
    
    
    tk.Tk().withdraw()      # there needs to be a window for filedialog to work, so hide it

    workers = multiprocessing.cpu_count()
    
    illegals = ['ancient_debris', 'anvil', 'banners', 'barrel', 'barrier', 'beacon', 'bee_nest', 'beehive', 'blast_furnace', 'brewing_stand', 'calibrated_sculk_sensor', 'campfire', 'chest', 'chiseled_bookshelf', 'command_block', 'chain_command_block', 'repeating_command_block', 'conduit', 'crafter', 'creaking_heart', 'crying_obsidian', 'daylight_detector', 'dispenser', 'dropper', 'enchanting_table', 'end_gateway', 'end_portal', 'end_portal_frame', 'ender_chest', 'furnace', 'grindstone', 'hanging_signs', 'hopper', 'jigsaw_block', 'jukebox', 'lectern', 'light_block', 'lodestone', 'nether_portal', 'netherite_block', 'obsidian', 'reinforced_deepslate', 'respawn_anchor', 'sculk_catalyst', 'sculk_sensor', 'sculk_shrieker', 'smoker', 'spawner', 'structure_block', 'trapped_chest', 'trial_spawner', 'vault']

    print("File to open:")
    file = filedialog.askopenfilename(filetypes=[("Litematica Files", "*.litematic")])

    origin = (int(input("Smallest X value in selection (Remember negative): ")), int(input("Smallest Y value in selection                    : ")), int(input("Smallest Z value in selection                    : ")))

    print("\nHere is the list of blocks being checked for:")
    time.sleep(1)
    for i in range(len(illegals)):      # cycle through and print all illegal blocks
        print(illegals[i], end=", ")    #
        if i%3 == 2:                    #
            print()                     #

    time.sleep(1)

    if input("\n\nWould you like to add/remove (a) block(s) from this list? (y/n): ").lower() == "y":
        answer = '.'
        while answer != '':
            answer = input("Add or remove block? (a/r): ").lower()
            if answer == "a":
                illegals.append(input("Block id of block to add (without 'minecraft:'): ").strip())
            elif answer == "r":
                illegals.remove(input("Block id of block to remove (without 'minecraft:'): ").strip())
                
    minimap = input("Are you using VoxelMap of Xaero's? (v/x): ").lower()


    print("Loading NBT from file...")
    TEMPfile = nbt.NBTFile(file, "rb")

    TEMPregionName = TEMPfile["Regions"].keys()[0]  # get the first region of the litematica file
    region = TEMPfile["Regions"][TEMPregionName]    # copy to new variable
    
    
    print("Creating illegals ID list...")
    palette = list(region["BlockStatePalette"])         # create a list of the IDs of all illegal blocks in the file for faster comparison (int comparasons faster than string comparasons)
    illegalPalette = []                                 #
    for i in range(len(palette)):                       #
        if palette[i]["Name"].value[10:] in illegals:   #
            illegalPalette.append(i)                    #
    

    sx = abs(region["Size"]["x"].value)     # litematica region sizes can be negative, so change that
    sy = abs(region["Size"]["y"].value)     #
    sz = abs(region["Size"]["z"].value)     #
    volume = sz*sy*sx       # total volume of blocks



def decodeAndCheck():
    global arr, nbits, palette, badBlocks
    print("Decoding and checking for bad blocks...")
    
    palette = region["BlockStatePalette"]
    
    nbits = max(math.ceil(math.log(len(list(palette)), 2)), 2)              # still got no idea what this does
    arr = [int(i) & ((1 << 64) - 1) for i in list(region["BlockStates"])]   #
    
    jobs: list[multiprocessing.Process] = []                    # list of processes
    pipes = []                                                  # list of pipes
    for i in range(workers):
        r,s = multiprocessing.Pipe(False)                       # create a pipe (r: receving pipe, s: sending pipe)
        p = multiprocessing.Process(target=worker, args=(s, i)) # create process with sending pipe
        jobs.append(p)                                          # add process to list
        pipes.append(r)                                         # receving pipe to list
        p.start()                                               # start process
        
    badBlocks = []
    for j in range(workers):
        badBlocks.extend(pipes[j].recv())   # get blocks from workers down pipes
        jobs[j].join()                      # wait till worker is done



def worker(pipe, id):
    each, extras = divmod(volume, workers)                              # find out what part of the blocks this worker is decoding
    sizes = ([0] + extras * [each + 1] + (workers-extras) * [each])     #
    points = np.array(sizes).cumsum()                                   #
        
    mask = (1 << nbits) - 1                                                                         # don't know how this works, got it from the 
    badBlocks = []                                                                                  # litemapy library and optimised it for preformance
    for i in range(points[id], points[id+1]):                                                       #
        startOff = i * nbits                                                                        #
        startArrIdx = startOff >> 6                                                                 #
        endArrIdx = ((i+1) * nbits - 1) >> 6                                                        #
        startBitOff = startOff & 0x3F                                                               #
        if startArrIdx == endArrIdx:                                                                #
            block = arr[startArrIdx] >> startBitOff & mask                                          #
        else:                                                                                       #
            block = (arr[startArrIdx] >> startBitOff | arr[endArrIdx] << (64 - startBitOff)) & mask #
        
        if block in illegalPalette:                                                                                                             # if block id in illegals
            badBlocks.append((palette[block]["Name"].value[10:], (i%sx + origin[0], int(i/(sx*sz)) + origin[0], int((i/sx)%sz) + origin[0])))   # add to illegals list
        
        if id == 0 and i%(sx*sz) == 0:                  # if this worker is worker 0 then print progress every now and then
            print(f"Approx: {(i/sizes[1]*100):.2f}%")   #
            
    print(f"Worker {id} done.")
    
    pipe.send(badBlocks)            # send found blocks down pipe to main program
    


def export():
    if minimap == "x": fileX = ".txt"
    elif minimap == "v": fileX = ".points"
    with open(filedialog.asksaveasfilename(filetypes=[("Text Files", f"*{fileX}"), ("All Files", "*.*")]), "w") as f:
        print(f"Writing to file {f.name}")
        if minimap == "x":
            f.write("#\n#waypoint:name:initials:x:y:z:color:disabled:type:set:rotate_on_tp:tp_yaw:visibility_type\n#")
            for b in badBlocks:
                f.write(f"\nwaypoint:{b[0]}:S:{b[1][0]}:{b[1][1]}:{b[1][2]}:13:false:0:gui.xaero_default:false:0:0")
        elif minimap == "v":
            for b in badBlocks:
                f.write(f"\nname:{b[0]},x:{b[1][0]},z:{b[1][2]},y:{b[1][1]},enabled:true,red:1.0,green:1.0,blue:1.0,suffix:,world:,dimensions:overworld#")




if __name__ == "__main__":
    init()
    startNs = time.time_ns()    # time in nanoseconds program started doing stuff automaticall
    decodeAndCheck()
    print(f"Read and analysed {volume:,} blocks in {timedelta(seconds=(time.time_ns() - startNs )/ 1000000000)} ({(time.time_ns() - startNs )/ 1000000000:.3f} seconds) finding {len(badBlocks)} illegal blocks.")
    export()
