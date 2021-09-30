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


def shuffleImagestoCZT(hyperStackImagePlus, case):
    #hyperStackImagePlus.show()
    #Inverser T (totalTime) et Z (zDepthByChannel)
    mainProcessor = hyperStackImagePlus.getProcessor()
    numberOfChannels = hyperStackImagePlus.getNChannels() #Nombre de canaux
    totalTime = hyperStackImagePlus.getNFrames()
    zDepthByChannel = hyperStackImagePlus.getNSlices()
    imageTitle = hyperStackImagePlus.getTitle()
    print("numberOfChannels: "+str(numberOfChannels))
    print("zDepthByChannel: "+str(zDepthByChannel))
    print("totalTime: "+str(totalTime))
    imageWidth = hyperStackImagePlus.getWidth(); #Largeur de l'image
    imageHeight = hyperStackImagePlus.getHeight(); #Hauteur de l'image
    bitDepth = hyperStackImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    stackedImages = hyperStackImagePlus.getStack()
    #totalNumberOfImages = mainImageStackImp.getStackSize() #Profondeur Z * Nombre de canaux * temps
    totalNumberOfImages = stackedImages.getSize() #Profondeur Z * Nombre de canaux * temps
    print("totalNumberOfImages: "+str(totalNumberOfImages))
    #print("Separating by channels...")

    C = 0
    T = 1
    Z = 2

    if case == "CTZ":
        first=C
        middle=T
        last=Z
        nFirst=numberOfChannels
        nMiddle=totalTime
        nLast=zDepthByChannel
    elif case == "ZCT":
        first=Z
        middle=C
        last=T
        nFirst=zDepthByChannel
        nMiddle=numberOfChannels
        nLast=totalTime
    elif case == "ZTC":
        first=Z
        middle=T
        last=C
        nFirst=zDepthByChannel
        nMiddle=totalTime
        nLast=numberOfChannels
    elif case == "TCZ":
        first=T
        middle=C
        last=Z
        nFirst=totalTime
        nMiddle=numberOfChannels
        nLast=zDepthByChannel
    elif case == "TZC":
        first=T
        middle=Z
        last=C
        nFirst=totalTime
        nMiddle=zDepthByChannel
        nLast=numberOfChannels
    else:
        first=C
        middle=Z
        last=T
        nFirst=numberOfChannels
        nMiddle=zDepthByChannel
        nLast=totalTime


    shuffledHyperStackImageStack = ImageStack()
    originalImageArray = stackedImages.getImageArray()
    pythonOriginalImageArray = []
    pythonShuffledImageArray = []
    for imageArray in originalImageArray:
        pythonOriginalImageArray.append(imageArray)
        pythonShuffledImageArray.append(imageArray)
    originalImageLabels = stackedImages.getSliceLabels()
    pythonOriginalLabelsArray = []
    pythonShuffledLabelsArray = []
    for imageLabel in originalImageLabels:
        pythonOriginalLabelsArray.append(imageLabel)
        pythonShuffledLabelsArray.append(imageLabel)

    indexes = [0, 0, 0]
    for timeNumber in range(0, totalTime):
        for zNumber in range(0, zDepthByChannel):
            for channelNumber in range(0, numberOfChannels):
                destinationSliceIndex = channelNumber + zNumber*numberOfChannels + timeNumber*numberOfChannels*zDepthByChannel
                #sourceSliceIndex = indexes[first] + indexes[middle]*nFirst + indexes[last]*nFirst*nMiddle
                sourceSliceIndex = channelNumber + timeNumber*nFirst + zNumber*nFirst*nMiddle
                print("destinationSliceIndex: "+str(destinationSliceIndex)+", sourceSliceIndex: "+str(channelNumber)+"+"+str(timeNumber)+"*"+str(nFirst)+"+"+str(zNumber)+"*"+str(nFirst)+"*"+str(nMiddle)+" = "+str(sourceSliceIndex))
                pythonOriginalImageArray[destinationSliceIndex] = pythonShuffledImageArray[sourceSliceIndex]
            	pythonOriginalLabelsArray[destinationSliceIndex] = pythonShuffledLabelsArray[sourceSliceIndex]
                indexes[0]+=1
            indexes[1]+=1
        indexes[2]+=1

                #print("selectedSliceNumber: "+str(sliceNumber))
                #sliceProcessor = stackedImages.getProcessor(sliceNumber)
                #shuffledHyperStackImageStack.addSlice(sliceProcessor)

    number = 0
    for sliceImageArray in pythonOriginalImageArray:
        if sliceImageArray == None:
            break
        sliceImage = IJ.createImage(str(pythonShuffledLabelsArray[number]), "16-bit Black", imageWidth, imageHeight, 1)
        sliceProcessor = sliceImage.getProcessor()
        sliceProcessor.setPixels(sliceImageArray)
        #print("sliceImageArray: "+str(sliceImageArray))
        shuffledHyperStackImageStack.addSlice(sliceProcessor)
        number+=1

    #for zNumber in range(0, zDepthByChannel):
        #for timeNumber in range(1, totalNumberOfImages+1, totalTime):
            #for channelNumber in range(timeNumber, totalNumberOfImages, numberOfChannels):
            #sliceNumber = timeNumber+zNumber
            #print("selectedSliceNumber: "+str(sliceNumber))
            #sliceProcessor = stackedImages.getProcessor(sliceNumber)
            #shuffledHyperStackImageStack.addSlice(sliceProcessor)




    """
    arrayOfChannels = []
    for channelNumber in range(0,numberOfChannels):
        channelStack = ImageStack(imageWidth, imageHeight)

        timeStacks = []
        for timeNumber in range(0, totalTime):
            timeStack = ImageStack(imageWidth, imageHeight)
            timeStacks.append(timeStack)

        for imageNumber in range(channelNumber, totalNumberOfImages, numberOfChannels):
            sliceTitle = stackedImages.getSliceLabel(imageNumber+1)
            sliceProcessor = stackedImages.getProcessor(imageNumber+1)
            channelStack.addSlice(sliceTitle, sliceProcessor)

        #channelImagePlus = ImagePlus("Test view content channel "+str(channelNumber), channelStack)
        #channelImagePlus.show()

        #OK jusque ici

        zDepthNumberCount = 0
        timeSliceCount = 0
        for sliceNumber in range(1, channelStack.getSize()+1):
            #print(str(zDepthNumberCount), str(timeSliceCount))
            sliceProcessor = channelStack.getProcessor(sliceNumber)
            selectedTimeStack = timeStacks[zDepthNumberCount]
            selectedTimeStack.addSlice(sliceProcessor)
            zDepthNumberCount+=1
            if zDepthNumberCount == totalTime: #zDepthByChannel
                zDepthNumberCount = 0
                timeSliceCount+=1
            if timeSliceCount == zDepthByChannel: #totalTime
                break

        timeImagePluses = []
        i=0
        #print("timeStacks: "+str(timeStacks))
        for timeStack in timeStacks:
            title = String("Channel "+str(channelNumber+1)+" - Time "+str(i))
            #print("title: "+str(title))
            timeImagePlus = ImagePlus(title, timeStack)
            #timeImagePlus.show()
            timeImagePluses.append(timeImagePlus)
            i+=1
        arrayOfChannels.append(timeImagePluses)
    #print("arrayOfChannels: "+str(arrayOfChannels))
    #print("Finished separating by channels")

    shuffledHyperStackImageStack = ImageStack()
    for timeStamp in range(totalTime):
        for zDepth in range(zDepthByChannel):
            for channelNumber in range(numberOfChannels):
                timeImagePlus = arrayOfChannels[channelNumber][timeStamp]
                print("timeImagePlus: "+str(timeImagePlus))
                #timeImagePlus.show()
                timeImageStack = timeImagePlus.getStack()
                timeImageStackSize = timeImageStack.getSize()
                timeImageSliceProcessor = timeImageStack.getProcessor(zDepth+1)
                shuffledHyperStackImageStack.addSlice(timeImageSliceProcessor)
    """

    shuffledHyperStackImagePlus = ImagePlus(imageTitle, shuffledHyperStackImageStack)
    #shuffledHyperStackImagePlus.show()
    shuffledHyperStackImagePlus = HyperStackConverter.toHyperStack(shuffledHyperStackImagePlus, nFirst, nMiddle, nLast, "Color")
    return shuffledHyperStackImagePlus


IJ.log('\\Clear') #efface le contenu de la console
hyperStackImagePlus = IJ.openImage()
hyperStackImagePlus.show()
#shuffledHyperStackImagePlus = shuffleImagestoCZT(hyperStackImagePlus, "CTZ")
HyperStackConverter.shuffle(hyperStackImagePlus, 1)
hyperStackImagePlus.show()
