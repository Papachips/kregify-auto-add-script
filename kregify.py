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
        if(os.path.splitext(file)[1] == '.tar'or os.path.splitext(file)[1] == '.7z'):
            filePath = directory + '/' + file
            archive = py7zr.SevenZipFile(filePath, mode='r')
            archive.extractall(path=directory)
            archive.close()
        if(os.path.splitext(file)[1] == '.zip'):
            with zipfile.ZipFile(directory + '/' + file, 'r') as zip:
                zip.extractall(directory)

    for path, subdirs, files in os.walk(directory):
        for name in files:
            file = os.path.join(path, name)
            os.chdir(path)

            try:
                os.chmod(file, stat.S_IWUSR|stat.S_IREAD)
                audioFile = eyed3.load(file)
                artistInfo[audioFile.tag.album] = audioFile.tag.artist
            except:
                #ignore garbage files and move on
                pass

            ext = os.path.splitext(file)[1]
            invalidExt = ['.jpg', '.png', '.url', '.tar', '.zip', '.7z']
            if ext in invalidExt:
                os.remove(file)

        os.system('cmd /c "filebot -rename *.mp3 --db ID3 -non-strict"') 

    #change directory so we have access to rename/delete
    os.chdir('C:\\')

    #update to reflect changes to directory
    fileList = os.listdir(directory)

    index = 0
    for file in fileList:
        filePath = directory + '\\' + file
        renamedPath = directory + '\\' +  re.sub('[\\/:"*?<>|]+', ' ', tuple(artistInfo.items())[index][-1])
        albumPath = os.path.join(renamedPath,tuple(artistInfo.items())[index][0])

        if(not os.path.isdir(albumPath)):
            os.rename(filePath, renamedPath)
            os.mkdir(albumPath)

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
