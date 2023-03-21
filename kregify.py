import os
import py7zr
import shutil
import eyed3
import glob
from distutils.dir_util import copy_tree
import zipfile
import stat
import re

def formatAndUpload():
    directory = 'DIRECTORY_PATH_HERE'
    server = 'SERVER_PATH_HERE'
    fileList = os.listdir(directory)
    artistInfo = dict()

    for file in fileList:
        #splits the file name and extension. py7zr handles .tar and .7z, so we check for those first as most often that's what we have.
        if(os.path.splitext(file)[1] == '.tar'or os.path.splitext(file)[1] == '.7z'):
            filePath = directory + '/' + file
            archive = py7zr.SevenZipFile(filePath, mode='r')
            archive.extractall(path=directory)
            archive.close()
            os.remove(filePath)

        #py7zr does not handle .zip files, so we use zipfile for that.
        if(os.path.splitext(file)[1] == '.zip'):
            with zipfile.ZipFile(directory + '/' + file, 'r') as zip:
                zip.extractall(directory)
                os.remove(filePath)

    #iterate over all the decompressed directories folders
    for path in glob.glob(directory + '/*/'):
        for folderPath in os.walk(path):
            #change directory so when filebot runs, it runs against the correct album directory
            os.chdir(folderPath[0])

            #folderPath is a tuple
            #folderPath[0] is our directory
            #folderPath[1] is blank
            #folderPath[2] is a list of track names
            for name in folderPath[2]:
                file = os.path.join(folderPath[0], name)
                try:
                    #ensure we have read/write ability on the files
                    os.chmod(file, stat.S_IWUSR|stat.S_IREAD)

                    #get artist meta data for folder naming
                    audioFile = eyed3.load(file)
                    artistInfo[audioFile.tag.album] = audioFile.tag.artist
                except:
                    #ignore garbage files, delete, and move on
                    ext = os.path.splitext(file)[1]
                    invalidExt = ['.jpg', '.png', '.url', '.tar', '.zip', '.7z']
                    if ext in invalidExt:
                        os.remove(file)
                    pass
        #calls filebot cli to properly set metadata on tracks
        os.system('cmd /c "filebot -rename *.mp3 --db ID3 -non-strict"') 

    #change directory so we have access to rename/delete
    os.chdir('C:\\')

    #update to reflect changes to directory
    fileList = os.listdir(directory)

    index = 0
    for file in fileList:
        filePath = directory + '\\' + file
        #make sure we remove unsafe characters for file/folder names
        renamedPath = directory + '\\' +  re.sub('[\\/:"*?<>|]+', ' ', tuple(artistInfo.items())[index][-1])
        albumPath = os.path.join(renamedPath,tuple(artistInfo.items())[index][0])

        #create folders for artist -> album directories pattern
        if(not os.path.isdir(albumPath)):
            os.rename(filePath, renamedPath)
            os.mkdir(albumPath)

        #get list of renamed tracks and move them to the newly created album folder
        songs = glob.glob(renamedPath +'\\' + '*.mp3')
        for song in songs:
            shutil.move(song, albumPath)

        #this handles multiple albums of the same artist.
        #moves the first over like normal.
        #if artist path exists it merges and then deletes the directory coming from the pc.
        try:
            shutil.move(renamedPath, server)
        except:
            copy_tree(renamedPath,server + '\\'+ tuple(artistInfo.items())[index][-1])
            shutil.rmtree(renamedPath)
        index += 1

formatAndUpload()
