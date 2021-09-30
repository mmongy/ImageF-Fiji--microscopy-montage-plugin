import os, sys
import java, jarray, array
#from jarray import array
import math
from java.awt import Frame, Dialog, Button
from java.awt.event import ActionEvent, ActionListener
from java.io import File
from java.lang import System, Integer
from ij import IJ, ImageStack, ImagePlus, ImageListener, VirtualStack, WindowManager
from ij.gui import GenericDialog
from ij.io import OpenDialog, FileSaver
from ij.plugin import LutLoader, ZProjector, HyperStackConverter
from ij.process import ImageProcessor, FloatProcessor, ShortProcessor, ByteProcessor
from fiji.util.gui import GenericDialogPlus
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.plugins.util import BFVirtualStack
from loci.formats import ImageReader, ChannelSeparator
from loci.formats.in import MetamorphReader


def openMainDialogBox():
    #od = OpenDialog("Selectionner un fichier")
    #folder = od.getDirectory()
    #IJ.log(folder);
    #filename = od.getFileName() #intérêt de récupérer le nom du fichier -> récupérer l'extension
    #extension = od.getFileName().split('.').pop() #Array.pop(). Pratique pour faire une fonction getExtension()
    #IJ.log(folder+filename)

    # Create an instance of GenericDialogPlus
    mainDialogBox = GenericDialogPlus("Restack Tiff deconvolved images from Huygens")
    mainDialogBox.addMessage("Ne fonctionnera correctement que si les noms des fichiers images de sortie de Huygens ont ete laisses intacts. Ne pas les modifier.")
    #mainDialogBox.addButton("Ouvrir image", imageSelectionListener())
    mainDialogBox.addMessage("------------------------------------------")
    mainDialogBox.addDirectoryField("Choisir un repertoire-cible", "None")
    mainDialogBox.addMessage("------------------------------------------")
    mainDialogBox.addDirectoryField("Choisir un repertoire pour deposer les piles d'images", "None")
    mainDialogBox.addMessage("------------------------------------------")

    #Select File Type
    choixType = ["1 fichier par canal (NOM_FICHIER_chXX.tif)", "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)", "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)", "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)"]
    selectionType = choixType[0]
    mainDialogBox.addChoice("Selectionner type de fichiers",choixType,selectionType)
    mainDialogBox.addMessage("------------------------------------------")

    choixDisplayMode = ["Color", "Greyscale", "Composite"]
    selectionDisplayModeDefaut = choixDisplayMode[0]
    mainDialogBox.addChoice("Color Display Mode",choixDisplayMode,selectionDisplayModeDefaut)
    mainDialogBox.addMessage("------------------------------------------")
    #Affichage de la boîte de dialogue
    mainDialogBox.showDialog();

    #Récupération choix
    folder = mainDialogBox.getNextString()
    save_folder = mainDialogBox.getNextString()
    vecteurChoix=mainDialogBox.getChoices()
    selectionTypeFichier = vecteurChoix[0]
    valeurSelectionTypeFichier = str(selectionTypeFichier.getSelectedItem())
    selectionDisplayMode = vecteurChoix[1]
    valeurSelectionDisplayMode = str(selectionDisplayMode.getSelectedItem())

    if mainDialogBox.wasCanceled() == True:
        print("Canceled, Values set to None")
        folder = None
        save_folder = None
        valeurSelectionTypeFichier = None
        valeurSelectionDisplayMode = None

    return folder, save_folder, valeurSelectionTypeFichier, valeurSelectionDisplayMode

def get_tif_files(folder):
    tifFileList = []
    for file in os.listdir(folder):
        if file.endswith(".tif"):
            tifFileList.append(file)
    return tifFileList

def getListOfFileNameRoots(ListOfTifFilesToDo, valeurSelectionTypeFichier):
    listOfFileNameRoots = []
    for tifFileToDo in ListOfTifFilesToDo:
        tifFileToDoParsedName = str(tifFileToDo).split("_")
        channelIdentifierExtension = tifFileToDoParsedName.pop(-1)
        channelIdentifier = channelIdentifierExtension.split(".")[0]
        if valeurSelectionTypeFichier == "1 fichier par canal (NOM_FICHIER_chXX.tif)":
            tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
        if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
            timeIdentifier = tifFileToDoParsedName.pop(-1)
            tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
        if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)":
            depthIdentifier = tifFileToDoParsedName.pop(-1)
            tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
        if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)":
            depthIdentifier = tifFileToDoParsedName.pop(-1)
            timeIdentifier = tifFileToDoParsedName.pop(-1)
            tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
        if tifFileToDoParsedNameCorrected not in listOfFileNameRoots:
            listOfFileNameRoots.append(tifFileToDoParsedNameCorrected)
    return listOfFileNameRoots

def orderChannelsInDictionary(ListOfTifFilesToDo, valeurSelectionTypeFichier):
    mainDictionary = {}
    listOfFileNameRoots = getListOfFileNameRoots(ListOfTifFilesToDo, valeurSelectionTypeFichier)
    for fileNameRoot in listOfFileNameRoots:
        fileChannelsDictionary = {}
        for tifFileToDo in ListOfTifFilesToDo:
            tifFileToDoParsedName = str(tifFileToDo).split("_")
            channelIdentifierExtension = tifFileToDoParsedName.pop(-1)
            channelIdentifier = channelIdentifierExtension.split(".")[0]
            if valeurSelectionTypeFichier == "1 fichier par canal (NOM_FICHIER_chXX.tif)":
                tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
                if str(tifFileToDoParsedNameCorrected) == str(fileNameRoot):
                    if str(channelIdentifier) not in sorted(fileChannelsDictionary.keys()):
                        fileChannelsDictionary[str(channelIdentifier)] = {}
                    fileChannelsDictionary[str(channelIdentifier)] = tifFileToDo
            if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
                timeIdentifier = tifFileToDoParsedName.pop(-1)
                tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
                if str(tifFileToDoParsedNameCorrected) == str(fileNameRoot):
                    if str(channelIdentifier) not in sorted(fileChannelsDictionary.keys()):
                        fileChannelsDictionary[str(channelIdentifier)] = {}
                    fileChannelsDictionary[str(channelIdentifier)][str(timeIdentifier)] = tifFileToDo
            if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)":
                depthIdentifier = tifFileToDoParsedName.pop(-1)
                tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
                if str(tifFileToDoParsedNameCorrected) == str(fileNameRoot):
                    if str(channelIdentifier) not in sorted(fileChannelsDictionary.keys()):
                        fileChannelsDictionary[str(channelIdentifier)] = {}
                    fileChannelsDictionary[str(channelIdentifier)][str(depthIdentifier)] = tifFileToDo
            if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)":
                depthIdentifier = tifFileToDoParsedName.pop(-1)
                timeIdentifier = tifFileToDoParsedName.pop(-1)
                tifFileToDoParsedNameCorrected = "_".join(tifFileToDoParsedName)
                if str(tifFileToDoParsedNameCorrected) == str(fileNameRoot):
                    if str(channelIdentifier) not in sorted(fileChannelsDictionary.keys()):
                        fileChannelsDictionary[str(channelIdentifier)] = {}
                    if str(depthIdentifier) not in sorted(fileChannelsDictionary[str(channelIdentifier)].keys()):
                        fileChannelsDictionary[str(channelIdentifier)][str(depthIdentifier)] = {}
                    if str(timeIdentifier) not in sorted(fileChannelsDictionary[str(channelIdentifier)][str(depthIdentifier)].keys()):
                        fileChannelsDictionary[str(channelIdentifier)][str(depthIdentifier)][str(timeIdentifier)] = {}
                    fileChannelsDictionary[str(channelIdentifier)][str(depthIdentifier)][str(timeIdentifier)] = tifFileToDo
            mainDictionary[str(fileNameRoot)] = fileChannelsDictionary
    return mainDictionary

def getDirectoryContent(folder, valeurSelectionTypeFichier):
    #fileList = os.listdir(folder) #= get_tif_files()

    ListOfTifFilesToDo = get_tif_files(folder)
    ListOfTifFilesToDo.sort()
    print("ListOfTifFilesToDo", str(ListOfTifFilesToDo))
    mainDictionary = orderChannelsInDictionary(ListOfTifFilesToDo, valeurSelectionTypeFichier) #Organise les noms des fichiers de façon à rassembler en une liste les canaux d'une seule image, chaque sera ajoutée à la liste d'assemblages de canaux.
    print("mainDictionary: "+str(mainDictionary))

    imagesList = []
    for mainFileKey in sorted(mainDictionary.keys()):
        fileChannelsDictionary = mainDictionary[mainFileKey]
        filesChannelsImpsDictionary = {}
        filesChannelsImpsList = []
        for channels_dict_key in sorted(fileChannelsDictionary.keys()): #Trie chaque liste de canaux pour les canaux soient dans le bon ordre
            numberOfChannels = len(fileChannelsDictionary[channels_dict_key])
            if valeurSelectionTypeFichier == "1 fichier par canal (NOM_FICHIER_chXX.tif)":
                seriesOfImageFile = openImageFile(folder, fileChannelsDictionary[channels_dict_key])
                filesChannelsImpsList.append(seriesOfImageFile[0])
            if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
                tTimesArray = []
                for timeKey in sorted(fileChannelsDictionary[channels_dict_key].keys()):
                    seriesOfImageFile = openImageFile(folder, fileChannelsDictionary[channels_dict_key][timeKey])
                    tTimesArray.append(seriesOfImageFile[0])
                tTimesArray.sort()
                filesChannelsImpsList.append(tTimesArray)
            if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)":
                zDepthsArray = []
                for zDepthKey in sorted(fileChannelsDictionary[channels_dict_key].keys()):
                    seriesOfImageFile = openImageFile(folder, fileChannelsDictionary[channels_dict_key][zDepthKey])
                    zDepthsArray.append(seriesOfImageFile[0])
                zDepthsArray.sort()
                filesChannelsImpsList.append(zDepthsArray)
            if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)":
                zDepthsArray = []
                for zDepthKey in sorted(fileChannelsDictionary[channels_dict_key].keys()):
                    tTimesArray = []
                    for timeKey in sorted(fileChannelsDictionary[channels_dict_key][zDepthKey].keys()):
                        seriesOfImageFile = openImageFile(folder, fileChannelsDictionary[channels_dict_key][zDepthKey][timeKey])
                        tTimesArray.append(seriesOfImageFile[0])
                    zDepthsArray.append(tTimesArray)
                filesChannelsImpsList.append(zDepthsArray)
            filesChannelsImpsDictionary[mainFileKey] = filesChannelsImpsList
        imagesList.append(filesChannelsImpsDictionary)
    return imagesList

def assembleChannelImagesInStacks(imageTitle, arrayOfImages, valeurSelectionDisplayMode, valeurSelectionTypeFichier):
    maxNumberOfChannels = len(arrayOfImages)
    maxNumberOfZDepth = 1;
    maxNumberOfTimeStamps = 1;
    print("assembleChannelImagesInStacks - arrayOfImages: "+str(arrayOfImages))
    for channelNumber in range(len(arrayOfImages)):
        if valeurSelectionTypeFichier == "1 fichier par canal (NOM_FICHIER_chXX.tif)":
            numberOfZDepth = len(arrayOfImages[channelNumber])
            if numberOfZDepth > maxNumberOfZDepth:
                maxNumberOfZDepth = numberOfZDepth
        if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
            numberOfZDepth = len(arrayOfImages[channelNumber])
            if numberOfZDepth > maxNumberOfZDepth:
                maxNumberOfZDepth = numberOfZDepth
            for zNumber in range(len(arrayOfImages[channelNumber])):
                numberOfTime = len(arrayOfImages[channelNumber][zNumber])
                if numberOfTime > maxNumberOfTimeStamps:
                    maxNumberOfTimeStamps = numberOfTime
        if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)":
            numberOfZDepth = len(arrayOfImages[channelNumber])
            if numberOfZDepth > maxNumberOfZDepth:
                maxNumberOfZDepth = numberOfZDepth
        if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)":
            numberOfZDepth = len(arrayOfImages[channelNumber])
            print(arrayOfImages[channelNumber])
            if numberOfZDepth > maxNumberOfZDepth:
                maxNumberOfZDepth = numberOfZDepth
            for zNumber in range(len(arrayOfImages[channelNumber])):
                print(arrayOfImages[channelNumber][zNumber])
                numberOfTime = len(arrayOfImages[channelNumber][zNumber])
                if numberOfTime > maxNumberOfTimeStamps:
                    maxNumberOfTimeStamps = numberOfTime

    hyperStack = ImageStack()
    #imageTitle = "HyperStack"
    print("C: "+str(maxNumberOfChannels)+", Z: "+str(maxNumberOfZDepth)+", T: "+str(maxNumberOfTimeStamps))
    for timeNumber in range(maxNumberOfTimeStamps):
        for zDepthNumber in range(maxNumberOfZDepth):
            for channelNumber in range(maxNumberOfChannels):
                #print("Position: "+str(channelNumber)+", "+str(zDepthNumber)+", "+str(timeNumber))
                currentImagePlus = arrayOfImages[channelNumber][zDepthNumber][timeNumber]
                #print("ImagePlus: "+str(currentImagePlus))
                currentImagePlus.setC(channelNumber)
                currentImagePlus.setZ(zDepthNumber)
                currentImagePlus.setT(timeNumber)
                currentImageProcessor = currentImagePlus.getProcessor()
                hyperStack.addSlice(currentImageProcessor)
    hyperStackImagePlus = ImagePlus(imageTitle, hyperStack)
    #hyperStackImagePlus.show()
    if maxNumberOfChannels*maxNumberOfZDepth*maxNumberOfTimeStamps > 1:
        converter = HyperStackConverter()
        hyperStackImagePlus = converter.toHyperStack(hyperStackImagePlus, maxNumberOfChannels, maxNumberOfZDepth, maxNumberOfTimeStamps, valeurSelectionDisplayMode)
        if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
            hyperStackImagePlus = converter.toHyperStack(hyperStackImagePlus, maxNumberOfChannels, maxNumberOfTimeStamps, maxNumberOfZDepth, "xyctz", valeurSelectionDisplayMode);

    return hyperStackImagePlus

def reListImagePluses(fileList, imageTitle, valeurSelectionDisplayMode, valeurSelectionTypeFichier):
    listOfOrderedImagePluses = []
    hyperStackList = []
    print("reListImagePluses - fileList: "+str(fileList))
    if valeurSelectionTypeFichier == "1 fichier par canal (NOM_FICHIER_chXX.tif)":
        channelsList = []
        channelNumber = 0
        for channelImagePlus in fileList:
            imageWidth = channelImagePlus.getWidth(); #Largeur de l'image
            imageHeight = channelImagePlus.getHeight(); #Hauteur de l'image
            zDepthByChannel = channelImagePlus.getNSlices() #Profondeur Z
            bitDepth = channelImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
            stackedImages = channelImagePlus.getStack()
            arrayOfImages = []
            for zNumber in range(1,zDepthByChannel+1):
                currentImageProcessor = stackedImages.getProcessor(zNumber)
                timeArray = []
                for timeNumber in range(1):
                    if bitDepth == 8:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "8-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 16:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "16-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 24: #RGB[img["Channel 1, Z-Depth 1" (-658), 16-bit, 840x840x1x1x1]]
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "RGB Black", imageWidth, imageHeight, 1)
                    if bitDepth == 32:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "32-bit Black", imageWidth, imageHeight, 1)
                    newImage.setProcessor(currentImageProcessor)
                    timeArray.append(newImage)
                arrayOfImages.append(timeArray)
            channelsList.append(arrayOfImages)
            channelNumber+=1
        hyperStackImagePlus = assembleChannelImagesInStacks(imageTitle, channelsList, valeurSelectionDisplayMode, valeurSelectionTypeFichier)
        hyperStackList.append(hyperStackImagePlus)
    if valeurSelectionTypeFichier == "1 fichier par canal + temps (NOM_FICHIER_tXX_chXX.tif)":
        channelsList = []
        channelNumber = 0
        for channelList in fileList:
            timeArray = []
            timeNumber = 0
            for timeImagePlus in channelList:
                imageWidth = timeImagePlus.getWidth(); #Largeur de l'image
                imageHeight = timeImagePlus.getHeight(); #Hauteur de l'image
                zDepthByChannel = timeImagePlus.getNSlices() #Profondeur Z
                bitDepth = timeImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
                stackedImages = timeImagePlus.getStack()
                arrayOfZDepths = []
                for zNumber in range(1,zDepthByChannel+1):
                    currentImageProcessor = stackedImages.getProcessor(zNumber)
                    if bitDepth == 8:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(timeNumber), "8-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 16:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(timeNumber), "16-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 24: #RGB[img["Channel 1, Z-Depth 1" (-658), 16-bit, 840x840x1x1x1]]
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(timeNumber), "RGB Black", imageWidth, imageHeight, 1)
                    if bitDepth == 32:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(timeNumber), "32-bit Black", imageWidth, imageHeight, 1)
                    newImage.setProcessor(currentImageProcessor)
                    arrayOfZDepths.append(newImage)
                timeNumber+=1
                timeArray.append(arrayOfZDepths)
            channelNumber+=1
            channelsList.append(timeArray)
        hyperStackImagePlus = assembleChannelImagesInStacks(imageTitle, channelsList, valeurSelectionDisplayMode, valeurSelectionTypeFichier)
        hyperStackList.append(hyperStackImagePlus)
    if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur (NOM_FICHIER_zXX_chXX.tif)":
        channelNumber = 0
        channelsList = []
        for channelList in fileList:
            zDepthArray = []
            zNumber = 1
            for zDepthImagePlus in channelList:
                timeArray = []
                for timeNumber in range(1):
                    imageWidth = zDepthImagePlus.getWidth(); #Largeur de l'image
                    imageHeight = zDepthImagePlus.getHeight(); #Hauteur de l'image
                    bitDepth = zDepthImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
                    currentImageProcessor = zDepthImagePlus.getProcessor()
                    if bitDepth == 8:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "8-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 16:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "16-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 24: #RGB[img["Channel 1, Z-Depth 1" (-658), 16-bit, 840x840x1x1x1]]
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "RGB Black", imageWidth, imageHeight, 1)
                    if bitDepth == 32:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber), "32-bit Black", imageWidth, imageHeight, 1)
                    newImage.setProcessor(currentImageProcessor)
                    timeArray.append(newImage)
                zNumber+=1
                zDepthArray.append(timeArray)
            channelNumber+=1
            channelsList.append(zDepthArray)
        hyperStackImagePlus = assembleChannelImagesInStacks(imageTitle, channelsList, valeurSelectionDisplayMode, valeurSelectionTypeFichier)
        hyperStackList.append(hyperStackImagePlus)
    if valeurSelectionTypeFichier == "1 fichier par canal et par profondeur + temps (NOM_FICHIER_tXX_zXX_chXX.tif)":
        channelNumber = 0
        channelsList = []
        for channelList in fileList:
            zDepthArray = []
            zNumber = 1
            for zDepthList in channelList:
                timeArray = []
                tTime = 1
                for timeImagePlus in zDepthList:
                    imageWidth = timeImagePlus.getWidth(); #Largeur de l'image
                    imageHeight = timeImagePlus.getHeight(); #Hauteur de l'image
                    bitDepth = timeImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
                    currentImageProcessor = timeImagePlus.getProcessor()
                    if bitDepth == 8:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(tTime), "8-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 16:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(tTime), "16-bit Black", imageWidth, imageHeight, 1)
                    if bitDepth == 24: #RGB[img["Channel 1, Z-Depth 1" (-658), 16-bit, 840x840x1x1x1]]
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(tTime), "RGB Black", imageWidth, imageHeight, 1)
                    if bitDepth == 32:
                        newImage = IJ.createImage(str(imageTitle)+" | Channel "+str(channelNumber)+", Z-Depth "+str(zNumber)+", T-time "+str(tTime), "32-bit Black", imageWidth, imageHeight, 1)
                    tTime+=1
                    newImage.setProcessor(currentImageProcessor)
                    timeArray.append(newImage)
                zNumber+=1
                zDepthArray.append(timeArray)
            channelNumber+=1
            channelsList.append(zDepthArray)
        hyperStackImagePlus = assembleChannelImagesInStacks(imageTitle, channelsList, valeurSelectionDisplayMode, valeurSelectionTypeFichier)
        hyperStackList.append(hyperStackImagePlus)
    return hyperStackList

def openImageFile(folder, imageFile):
    folder = folder.decode('utf8')
    imageFile = imageFile.decode('utf8')
    imagePath = str(folder)+"/"+str(imageFile)
    reader, options = readImageFile(imagePath)
    seriesCount = reader.getSeriesCount() #Nombre de séries
    zDepthByChannel = reader.getSizeZ() #Profondeur Z
    #imageStackImps = BF.openImagePlus(options)
    seriesOfImageFile = []
    for numberSerie in range(seriesCount):
        options.setSeriesOn(numberSerie,True); #Pour LIF - compter les séries - https://gist.github.com/ctrueden/6282856
        imageStackImps = BF.openImagePlus(options);
        #print imageStackImps
        mainImageStackImp = imageStackImps[-1] #0
        mainImageStackImp.setTitle(str(imageFile)+"_"+str(numberSerie))
        seriesOfImageFile.append(mainImageStackImp)
    #return mainImageStackImp
    return seriesOfImageFile

def readImageFile(imageFile):
    #IJ.log(imageFile)
    #print(imageFile)
    extension = imageFile.split('.').pop() #Array.pop(). Pratique pour faire une fonction getExtension()
    options = ImporterOptions()
    options.setId(imageFile)
    if extension == "nd":
        reader = MetamorphReader()
    else:
        reader = ImageReader()
    reader.setId(imageFile)
    return reader, options

def saveFileImage(imagePlus, dumpSaveFilePath, dumpFileName):
    fileSaver = FileSaver(imagePlus)
    imageName = imagePlus.getTitle()
    #File.makeDirectory(dumpDirectory)
    dumpFileString = str(dumpSaveFilePath)+"/"+str(imageName)+"_"+str(dumpFileName)
    #filestring=File.openAsString(dumpFileString);
    #dumpFileString = str(dumpDirectory)
    #fileSaver.saveAsTiff(dumpFileString)
    #IJ.saveAsTiff(imagePlus,dumpFileString)
    IJ.saveAs(imagePlus, "Tiff", dumpFileString);
    # ok = False
    # if (imagePlus.getStackSize() > 1):
    #      ok = fileSaver.saveAsTiffStack(imagePlus.getTitle());
    # else:
    #      ok = fileSaver.saveAsTiff(imagePlus.getTitle());
	#  	#The following call throws a NoSuchMethodError.
	#  	#ok = IJ.saveAsTiff(imp, settings.imageFilename);
    # if (ok==False):
    #      IJ.log("Failed to save image to file: " + imagePlus.getTitle());



###MAIN###

def run_script():
    IJ.log('\\Clear') #efface le contenu de la console

    your_os = System.getProperty("os.name");
    print(your_os)

    folder, dumpSaveFilePath, valeurSelectionTypeFichier, valeurSelectionDisplayMode = openMainDialogBox()

    if folder is None or dumpSaveFilePath is None or valeurSelectionDisplayMode is None:
        print("Cancel, End of Script")
        return

    if your_os == "Windows" or your_os == "Windows 10":
        separator = "\\"
    elif your_os == "Unix" or your_os == "Linux" or your_os == "Mac OS X":
        separator = "/"

    fileItems = getDirectoryContent(folder, valeurSelectionTypeFichier)
    print("fileItems: "+str(fileItems))
    for fileDirectory in fileItems:
        for mainFileName in fileDirectory.keys():
            imageTitle = str(mainFileName)
            impList = fileDirectory[imageTitle]
            listOfOrderedImagePluses = reListImagePluses(impList, imageTitle, valeurSelectionDisplayMode, valeurSelectionTypeFichier)
            print("listOfOrderedImagePluses: "+str(listOfOrderedImagePluses))
            for listedImagePlus in listOfOrderedImagePluses:
                saveFileImage(listedImagePlus, dumpSaveFilePath, valeurSelectionDisplayMode)

    print("End")

# If a Jython script is run, the variable __name__ contains the string '__main__'.
# If a script is loaded as module, __name__ has a different value.
if __name__ in ['__builtin__','__main__']:
    run_script()
