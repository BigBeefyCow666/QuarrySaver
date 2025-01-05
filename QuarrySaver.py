from nbt import nbt                 # for decoding nbt from litematica file
import numpy as np
import math as ma                   # math (duh)
import time
import os
import multiprocessing              # for cpu count
import tkinter as tk                # for file selector
from tkinter import filedialog      # 
from datetime import timedelta      # for converting to hh:mm:ss format (couldn't be bothered doing it myself)

os.environ["RAY_DEDUP_LOGS"]="0"                    # disable grouping of worker messages
os.environ["RAY_memory_monitor_refresh_ms"]="0"     # disable OOM errors (and pray nothing breaks)

import ray      # worker clustering for multicored program

tk.Tk().withdraw()      # there needs to be a window for filedialog to work, so hide it

workers = multiprocessing.cpu_count()

cpus = input("How many CPUs would you like to use? (just press ENTER for all): ")

try: workers = int(cpus)
except: pass

ray.init(num_cpus=workers)      # start ray instance


illegals = ['ancient_debris', 'anvil', 'banners', 'barrel', 'barrier', 'beacon', 'bee_nest', 'beehive', 'blast_furnace', 'brewing_stand', 'calibrated_sculk_sensor', 'campfire', 'chest', 'chiseled_bookshelf', 'command_block', 'chain_command_block', 'repeating_command_block', 'conduit', 'crafter', 'creaking_heart', 'crying_obsidian', 'daylight_detector', 'dispenser', 'dropper', 'enchanting_table', 'end_gateway', 'end_portal', 'end_portal_frame', 'ender_chest', 'furnace', 'grindstone', 'hanging_signs', 'hopper', 'jigsaw_block', 'jukebox', 'lectern', 'light_block', 'lodestone', 'nether_portal', 'netherite_block', 'obsidian', 'reinforced_deepslate', 'respawn_anchor', 'sculk_catalyst', 'sculk_sensor', 'sculk_shrieker', 'smoker', 'spawner', 'structure_block', 'trapped_chest', 'trial_spawner', 'vault']

print("File to open:")
TEMPfile = nbt.NBTFile(filedialog.askopenfilename(filetypes=[("Litematica Files", "*.litematic")]), "rb")

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




TEMPregionName = TEMPfile["Regions"].keys()[0]  # get the first region of the litematica file
region = TEMPfile["Regions"][TEMPregionName]    # copy to new variable

del TEMPfile, TEMPregionName                    # delete old NBT variables, as they take up alot of memory

sx = abs(region["Size"]["x"].value)     # litematica region sizes can be negative, so change that
sy = abs(region["Size"]["y"].value)     #
sz = abs(region["Size"]["z"].value)     #
volume = sz*sy*sx       # total volume of blocks




### multicored worker programs ###
@ray.remote
def blockDecoders(id, it: int, nbits: int): # block decoding
    each, extras = divmod(volume, workers)                              # find out what part of the blocks this worker is decoding
    sizes = ([0] + extras * [each + 1] + (workers-extras) * [each])     #
    points = np.array(sizes).cumsum()                                   #
    
    arr = ray.get(id[0])        # get the array from global ray store
    
    mask = (1 << nbits) - 1                                                                                     # don't know how this works, got it from the 
    sect = []                                                                                                   # litemapy library and optimised it for preformance
    for i in range(points[it], points[it+1]):                                                                   #
        startOff = i * nbits                                                                                    #
        startArrIdx = startOff >> 6                                                                             #
        endArrIdx = ((i+1) * nbits - 1) >> 6                                                                    #
        startBitOff = startOff & 0x3F                                                                           #
                                                                                                                #
        if startArrIdx == endArrIdx:                                                                            #
            sect.append(arr[startArrIdx] >> startBitOff & mask)                                                 #
        else:                                                                                                   #
            sect.append((arr[startArrIdx] >> startBitOff | arr[endArrIdx] << (64 - startBitOff)) & mask)        #
        
        if it == 0 and i%(sx*sz) == 0:                          # if this worker is worker 0 then print progress every now and then
            print(f"Decoded approx: {(i/sizes[1]*100):.2f}%")   #
            
    print(f"Worker {it} done.")     # say that this worker is done decoding

    return sect     # return my part of decoded blocklist

@ray.remote
def blockCheckers(listIDs:list, it: int):   # block checking
    badBlocks = []
    each, extras = divmod(sy, workers)                                  # find out what part of blocks this worker is checking
    sizes = ([0] + extras * [each + 1] + (workers - extras) *[each])    #
    points = np.array(sizes).cumsum()                                   #
    
    blocks = ray.get(listIDs[it])   # get my part of the blocks from global store
    
    for y in range(points[it], points[it+1]):   # for y in the part im decoding
        for z in range(sz):                     # for z
            for x in range(sx):                 # for x
                name = palette[blocks[y-points[it]][z][x]]["Name"].value[10:]           # get the block name from the palette
                if name in illegals:
                    badBlocks.append((name, (x+origin[0], y+origin[1] ,z+origin[2])))   # add name, x, y and z to illegal block list
        if it == 0:                                             # if worker 0 print status
            print(f"Checked approx: {(y/sizes[1]*100):.2f}%")   #

    print(f"Worker {it} done.")     # say this worker is done
    return badBlocks                # return my found illegal blocks
        



startNs = time.time_ns()    # time in nanoseconds program started doing stuff automatically


def getBlocks(blocklist, palette):
    print(f"Splitting job to {workers} workers and decoding {volume:,} blocks from NBT...")
    nbits = max(ma.ceil(ma.log(len(palette), 2)), 2)            # still got no idea what this does
    arr = [int(i) & ((1 << 64) - 1) for i in blocklist]         #
    
    id = [ray.put(arr)]     # put the big array thing into global store
    del arr
    
    job = [blockDecoders.remote(id, i, nbits) for i in range(workers)]      # crate worker job
        
    combined = []
    it = 1
    for part in ray.get(job):               # ray.get(job) returns the things the workers returned in order
        print(f"Combining block {it}...")
        combined.extend(part)
        it+=1
    
    ray.shutdown()      # shutdown and kill all workers to clear memory (this is needed, my computer did crash)
    
    del job
    
    print("Reshaping list into 3D array...")
    
    return combined


TEMPblockList = np.array(getBlocks(list(region["BlockStates"]), list(region["BlockStatePalette"]))).reshape((sy,sz,sx)) # blocks are in format y, z, x


print(f"splitting blocklist to {workers} workers...")


ray.init(num_cpus=workers)      # restart ray instance after shuting it down

ids = []
for part in np.array_split(TEMPblockList, workers):     # split the list of blocks
    ids.append(ray.put(part))                           # put each part of split blocks and global ray store and add the store id to a list

del TEMPblockList   # another large variable we don't need

palette = region["BlockStatePalette"]
job = [blockCheckers.remote(ids, i) for i in range(workers)]    # create block checking job

print("Analysing for bad blocks...")

badBlocks = []
it = 1
for part in ray.get(job):                       # run and get result of block checking job
    print(f"Combining blocks from worker {it}")   #
    badBlocks.extend(part)                      #
    it+=1

del palette     # clean up
ray.shutdown()  #
del job

print(f"Read and analysed {volume:,} blocks in {timedelta(seconds=(time.time_ns() - startNs )/ 1000000000)} ({(time.time_ns() - startNs )/ 1000000000:.3f} seconds) finding {len(badBlocks)} illegal blocks.")


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
