#-*- coding: utf-8 -*-

import os, sys
import java, jarray, array
#from jarray import array
import math
from java.io import File
from java.lang import Integer, String
from java.awt import Frame, Dialog, Button, Color, GridBagConstraints, Insets
from java.awt.event import ActionEvent, ActionListener, MouseAdapter, AdjustmentListener
from javax.swing import JDialog, JFrame, JPanel, JTabbedPane, JScrollPane, JLabel, JButton, JTextField, JSlider, JColorChooser, JComboBox, ImageIcon
from javax.swing.event import ChangeEvent, ChangeListener
from ij import IJ, ImageStack, ImagePlus, CompositeImage, ImageListener, VirtualStack, WindowManager
from ij.gui import GenericDialog
from ij.io import OpenDialog, FileSaver
from ij.plugin import LutLoader, ZProjector, HyperStackConverter
from ij.process import ImageProcessor, FloatProcessor, ShortProcessor, ByteProcessor, LUT
from fiji.util.gui import GenericDialogPlus
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.plugins.util import BFVirtualStack
from loci.formats import ImageReader, ChannelSeparator
from loci.formats.in import MetamorphReader

#from com.jidesoft.swing import RangeSlider #http://www.jidesoft.com/javadoc/com/jidesoft/swing/RangeSlider.html

import histogram2.HistogramMatcher

your_os = System.getProperty("os.name");
print(your_os)
if your_os == "Windows" or your_os == "Windows 10":
    separator = "\\"
elif your_os == "Unix" or your_os == "Linux" or your_os == "Mac":
    separator = "/"

"""
class imageSelectionListener(ActionListener):
    def actionPerformed(self,event):
        if event.getActionCommand() == "Ouvrir image":
            impList = getDirectoryContent()
        return impList

class parameterModificationListener(ImageListener):
    def __init__(self, imagePlus):
        self.imagePlus = imagePlus
    def imageClosed(self, imagePlus):
        if imagePlus == self.imagePlus:
            imagePlus.removeImageListener(self)
    def imageUpdated(self, imagePlus):
        if imagePlus == self.imagePlus:
            self.updateAndDraw()


class ScreenMouseListener(MouseAdapter):
    def mousePressed(self, event):
        print("Mouse pressed")
    def mouseReleased(self, event):
        print("Mouse released")

class SliderListener(ChangeListener):
    def stateChanged(self, event):
            value = event.getSource().getValue()
            event.getSource().setValue(value)
"""
#https://imagej.net/Find_Dimension_of_Raw_Image

class ViewedImageSelector:
    def __init__(self, selectedPath, metamorphBoolean):
        self.selectedPath = selectedPath
        self.metamorphBoolean = metamorphBoolean
        self.imageDictionary, self.imageFileList = self.getImpList()
        self.imageFilesDropDownList = self.makeImageFileDropdownList()
        self.zProjectDropdownList = self.makeZProjectDropdownList()

        self.selectedImageFileName = self.imageFileList[0]
        self.selectedImageFileSeries = self.imageDictionary[self.selectedImageFileName]
        self.selectedSerie = 1
        self.selectedImagePlus = self.selectedImageFileSeries[self.selectedSerie-1]
        self.selectedZProjectMethodName = "---No_Z-Project---"
        self.selectedZDepth = 1
        self.channelTunersArray, self.resultImageIcon, self.montageTuner = self.createChannelTunersArray()
        #self.zDepthSlider = TuningSlider(0, self.zDepthByChannel, self.selectedZDepth)
        #self.zDepthSlider = TuningSlider(0, self.selectedImagePlus.getNSlices()-1, self.selectedZDepth)

    def getImageDictionary(self):
        return self.imageDictionary

    def getImageFilesList(self):
        return self.imageFileList

    def getImpList(self):
        if self.metamorphBoolean == False:
            imageDictionary, imageFileList = self.getDirectoryContent()
        if self.metamorphBoolean == True:
            imageDictionary, imageFileList = self.getMetamorphDirectoryContent()
        print("imageDictionary: "+str(imageDictionary))
        print("imageFileList: "+str(imageFileList))
        return imageDictionary, imageFileList

    def getDirectoryContent(self):
        imageDictionary = {}
        impList=[]
        fileList = os.listdir(self.selectedPath)
        fileOnlyList = []
        for item in fileList:
            if os.path.isfile(str(self.selectedPath)+str(separator)+str(item)) == True:
                fileOnlyList.append(item)
        #print(fileList)
        for fileName in fileOnlyList:
            #file = str(folder)+"/"+str(file)
            seriesOfImageFile = self.openImageFile(fileName)
            imageDictionary[fileName] = seriesOfImageFile
        return imageDictionary, fileOnlyList

    def getMetamorphDirectoryContent(self):
        #Voir https://forum.image.sc/t/cannot-import-nd-files-via-fiji-macro/26150/3
        imageDictionary = {}
        metamorphList = []
        fileList = os.listdir(self.selectedPath)
        fileOnlyList = []
        for item in fileList:
            if os.path.isfile(str(self.selectedPath)+str(separator)+str(item)) == True:
                fileOnlyList.append(item)

        for file in fileOnlyList:
            extension = file.split('.').pop() #Array.pop(). Pratique pour faire une fonction getExtension()
            if extension == "nd":
                metamorphList.append(file)
                seriesOfImageFile = self.openImageFile(file)
                imageDictionary[file] = seriesOfImageFile
        return imageDictionary, metamorphList

    def openImageFile(self, imageFileName):
        #IJ.log(imageFile)
        imageFilePath = str(self.selectedPath)+str(separator)+str(imageFileName)
        print("imageFileName: "+str(imageFileName))
        print("imageFilePath: "+str(imageFilePath))
        imageId = imageFilePath
        print("imageId: "+str(imageId))
        #extension = imageFileName.split('.').pop() #Array.pop(). Pratique pour faire une fonction getExtension()

        if self.metamorphBoolean == True: #if extension == "nd":
            reader = MetamorphReader()
        else:
            reader = ImageReader()
        reader.setId(imageId)
        seriesCount = reader.getSeriesCount() #Nombre de séries
        zDepthByChannel = reader.getSizeZ() #Profondeur Z
        seriesOfImageFile = []
        options = ImporterOptions()
        options.setId(imageId)
        for numberSerie in range(seriesCount):
            options.setSeriesOn(numberSerie,True); #Pour LIF - compter les séries - https://gist.github.com/ctrueden/6282856
            imageStackImps = BF.openImagePlus(options);
            #print imageStackImps
            mainImageStackImp = imageStackImps[-1] #0
            mainImageStackImp.setTitle(str(imageFileName)+"_"+str(numberSerie))
            seriesOfImageFile.append(mainImageStackImp)
        return seriesOfImageFile

    def openSerieOfImageFile(self):
        mainImageStackImp = imageStackImps[0]
        return mainImageStackImp

    def makeImageFileDropdownList(self):
        choixImage = self.imageFileList
        return JComboBox(choixImage)

    def setSelectedImageFile(self, newImageFile):
        self.selectedImageFile = newImageFile

    def setSelectedSerie(self, newSelectedSerie):
        self.selectedSerie = newSelectedSerie

    def getSelectedImagePlus(self):
        return self.selectedImagePlus

    def loadNewImageFile(self, newSelectedImageFile):
        self.selectedImageFileName = newSelectedImageFile
        print("Nouveau fichier image: "+str(self.selectedImageFileName))
        self.selectedImageFileSeries = self.imageDictionary[self.selectedImageFileName]
        self.selectedSerie = 1
        self.loadSerieFromImageFile(self.selectedSerie)

    def loadSerieFromImageFile(self, newSerieNumber):
        self.selectedImagePlus = self.selectedImageFileSeries[newSerieNumber-1]
        print("Serie selectionnée: "+str(newSerieNumber)+", Contenu: "+str(self.selectedImagePlus))
        self.selectedZProjectMethodName = "---No_Z-Project---"
        self.selectedZDepth = 1
        self.channelTunersArray, self.resultImageIcon, self.montageTuner = self.createChannelTunersArray()
        self.setSelectedZProjectMethodName(self.selectedZProjectMethodName)
        for channelTuner in self.channelTunersArray:
            channelTuner.setSelectedZDepth(self.selectedZDepth)
            channelTuner.setSelectedZProjectMethodName(self.selectedZProjectMethodName)
        self.refreshAllIcons()

    def refreshAllIcons(self): #Discordance between shown icon (not refreshed) and image associated to shown icon (refreshed)
        for channelTuner in self.channelTunersArray:
            channelTuner.refreshPreviewIcon()
        self.resultImageIcon.refreshPreviewIcon()
        #self.resultImageIcon.getShownIconImage().show()
        self.montageTuner.refreshPreviewIcon()

    def openImageFileSelector(self, event):
        self.imageFileSelectorDialogBox = GenericDialogPlus("Choix fichier image")
        #print("Layout: "+str(self.imageFileSelectorDialogBox.getLayout()))
        channelCustomLutSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        self.imageFileSelectorDialogBox.add(self.imageFilesDropDownList, channelCustomLutSelectorConstraints)
        self.imageFileSelectorDialogBox.showDialog();
        if self.imageFileSelectorDialogBox.wasOKed():
            newSelectedImageFile = self.imageFilesDropDownList.getSelectedItem()
            self.loadNewImageFile(newSelectedImageFile)


    def getValuesFromSliders(self):
        vecteurSliders = self.imageFileSerieSelectorDialogBox.getSliders()
        serieValues = []
        for valueNumber in range(0,len(vecteurSliders)):
            serieValue = vecteurSliders[valueNumber].getValue()
            serieValues.append(serieValue)
        return serieValues

    def openImageFileSerieSelector(self, event):
        self.imageFileSerieSelectorDialogBox = GenericDialogPlus("Choisir serie")
        #print("Layout: "+str(self.imageFileSerieSelectorDialogBox.getLayout()))
        #imageFileSerieSelectoConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        minNbSeries = 1
        maxNbSeries = len(self.selectedImageFileSeries)
        self.imageFileSerieSelectorDialogBox.addSlider("Serie", minNbSeries, maxNbSeries, self.selectedSerie)
        self.imageFileSerieSelectorDialogBox.showDialog();
        if self.imageFileSerieSelectorDialogBox.wasOKed():
            serieValues = self.getValuesFromSliders()
            newSerieNumber = serieValues[0]
            self.loadSerieFromImageFile(newSerieNumber)

    def createChannelTunersArray(self):
        selectedImageAndSerieArrayOfChannels = separateByChannels(self.selectedImagePlus)
        channelTunersArray = []
        for channelNumber in range(0,len(selectedImageAndSerieArrayOfChannels)):
            channelImage = selectedImageAndSerieArrayOfChannels[channelNumber]
            channelTuner = ChannelPseudoColorTuner(channelImage, self.selectedZDepth, self.selectedZProjectMethodName)
            channelTunersArray.append(channelTuner)
        resultImageIcon = ResultImagePreviewIcon(channelTunersArray)
        montageTuner = MontageParametersTuner(channelTunersArray, resultImageIcon)
        return channelTunersArray, resultImageIcon, montageTuner

    def getChannelTunersArray(self):
        return self.channelTunersArray

    def getResultImageIcon(self):
        return self.resultImageIcon

    def getMontageTuner(self):
        return self.montageTuner

    def getSelectedZDepth(self):
        self.selectedZDepth

    def getSelectedZProjectMethodName(self):
        return self.selectedZProjectMethodName

    def setSelectedZDepth(self, newZDepth):
        self.selectedZDepth = newZDepth

    def setSelectedZProjectMethodName(self, newZProjectMethodName):
        self.selectedZProjectMethodName = newZProjectMethodName

    def makeZProjectDropdownList(self):
        choixZProject = ["---No_Z-Project---", "max", "min", "sum", "average", "median"]
        return JComboBox(choixZProject)

    def openZProjectMethodSelector(self, event):
        self.zProjectMethodSelectorDialogBox = GenericDialogPlus("Z-Project")
        #print("Layout: "+str(self.zProjectMethodSelectorDialogBox.getLayout()))
        zProjectMethodSelectorDialogBox = GridBagConstraints(gridx = 1, gridy = 1)
        self.zProjectMethodSelectorDialogBox.add(self.zProjectDropdownList, zProjectMethodSelectorDialogBox)
        self.zProjectMethodSelectorDialogBox.showDialog();
        if self.zProjectMethodSelectorDialogBox.wasOKed():
            newZProjectMethodName = self.zProjectDropdownList.getSelectedItem()
            self.setSelectedZProjectMethodName(newZProjectMethodName)
            for channelTuner in self.channelTunersArray:
                channelTuner.setSelectedZProjectMethodName(newZProjectMethodName)
            self.refreshAllIcons()

    def getValuesFromSliders(self):
        vecteurSliders = self.zDepthTunerDialogBox.getSliders()
        zDepthValues = []
        for valueNumber in range(0,len(vecteurSliders)):
            zDepthValue = vecteurSliders[valueNumber].getValue()
            zDepthValues.append(zDepthValue)
        return zDepthValues

    def openZDepthSelector(self, event):
        self.zDepthTunerDialogBox = GenericDialogPlus("Profondeur Z")
        #print("Layout: "+str(self.zDepthTunerDialogBox.getLayout()))
        #zDepthTunerDialogBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        minZDepth = 1
        maxZDepth = self.selectedImagePlus.getNSlices()
        self.zDepthTunerDialogBox.addSlider("Profondeur Z", minZDepth, maxZDepth, self.selectedZDepth)
        self.zDepthTunerDialogBox.showDialog();
        if self.zDepthTunerDialogBox.wasOKed():
            zDepthValues = self.getValuesFromSliders()
            newZDepth = zDepthValues[0]
            self.setSelectedZDepth(newZDepth)
            for channelTuner in self.channelTunersArray:
                channelTuner.setSelectedZDepth(newZDepth)
            self.refreshAllIcons()

    def addToJavaWindow(self, javaWindow):
        imageFileSelectorButton = JButton("Select image file", actionPerformed = self.openImageFileSelector)
        imageFileSerieSelectorButton = JButton("Select serie", actionPerformed = self.openImageFileSerieSelector)
        zProjectMethodButton = JButton("Select Z-Project method", actionPerformed = self.openZProjectMethodSelector)
        zDepthButton = JButton("Change Z-Depth", actionPerformed = self.openZDepthSelector)
        gridBagConstraints = GridBagConstraints()
        gridBagConstraints.gridx = GridBagConstraints.RELATIVE
        gridBagConstraints.insets.left = 10;
        self.resultImageIcon.addToJavaWindow(javaWindow)
        javaWindow.add(imageFileSelectorButton, gridBagConstraints)
        javaWindow.add(imageFileSerieSelectorButton, gridBagConstraints)
        javaWindow.add(zProjectMethodButton, gridBagConstraints)
        javaWindow.add(zDepthButton, gridBagConstraints)


class ChannelPseudoColorTuner:
    channel_tuner_number_count = 0
    #resultImagePlus
    def __init__(self, channelImagePlus, selectedZDepth, selectedZProjectMethodName):
        self.channel_tuner_number = ChannelPseudoColorTuner.channel_tuner_number_count

        self.channelImagePlus = channelImagePlus
        self.selectedZDepth = selectedZDepth
        self.selectedZProjectMethodName = selectedZProjectMethodName

        self.channelLutColorSelector = JColorChooser()
        self.lutDropdownList = self.makeLutList()
        self.selectedPseudoColor = self.channelLutColorSelector.getColor() #Couleur par défaut: Color(255, 255, 255) - Blanc
        self.selectedCustomLUT = self.lutDropdownList.getItemAt(0)
        self.selectedMinPixelValue = self.channelImagePlus.getProcessor().getMin()
        self.selectedMaxPixelValue = self.channelImagePlus.getProcessor().getMax()

        self.shownIconChannelTextDescription = "Preview, Channel "+str(self.channel_tuner_number_count)
        self.shownIconImage = self.makeShownChannelImage()
        self.shownIcon = self.createIconFromImagePlus()
        self.shownIconJLabel = JLabel(self.shownIcon)

        self.channelLutColorSelectorButton = JButton("Channel Color", actionPerformed = self.openColorChooser)
        self.channelLutCustomLUTSelectorButton = JButton("Select custom LUT", actionPerformed = self.openLutChooser)
        self.channelPixelBoundaryValuesTunerButton = JButton("Tune Min/Max pixel values", actionPerformed = self.openPixelBoundaryValuesTuner)
        self.imageJDisplayButton = JButton("Open on ImageJ/Fiji", actionPerformed = self.openInImageJ)

        ChannelPseudoColorTuner.channel_tuner_number_count+=1

    def setSelectedZDepth(self, newZDepth):
        self.selectedZDepth = newZDepth
        self.refreshPreviewIcon()

    def setSelectedZProjectMethodName(self, newZProjectMethodName):
        self.selectedZProjectMethodName = newZProjectMethodName
        self.refreshPreviewIcon()

    def refreshPreviewIcon(self):
        self.shownIconImage = self.makeShownChannelImage()
        newShownIcon = self.createIconFromImagePlus()
        self.setImageIcon(newShownIcon)

    def setImageIcon(self, newShownIcon):
        self.shownIconJLabel.setIcon(newShownIcon)

    def makeShownChannelImage(self):
        channelImageWidth = self.channelImagePlus.getWidth()
        channelImageHeight = self.channelImagePlus.getHeight()
        if self.selectedZProjectMethodName == "---No_Z-Project---":
            zNumber = self.selectedZDepth
            zStack = self.channelImagePlus.getStack()
            shownImageProcessor = zStack.getProcessor(zNumber)
        if self.selectedZProjectMethodName != "---No_Z-Project---":
            zNumber = 1
            zProjectImage = makeZProjectOnSingleChannel(self.channelImagePlus, self.selectedZProjectMethodName)
            shownImageProcessor = zProjectImage.getProcessor()
        shownImage = IJ.createImage("Z-Project "+str(self.selectedZProjectMethodName)+"Z-Number: "+str(zNumber), "RGB Black", channelImageWidth, channelImageHeight, 1)
        shownImage.setProcessor(shownImageProcessor)
        shownPseudoColoredChannelImagePlus = makeChannelTuningPipeline(shownImage, self.channel_tuner_number, self.selectedPseudoColor, self.selectedCustomLUT, self.selectedMinPixelValue, self.selectedMaxPixelValue, self.selectedZProjectMethodName)
        return shownPseudoColoredChannelImagePlus

    def createIconFromImagePlus(self):
        previewAWTimage = self.shownIconImage.getImage()
        shownIconWidth = int(self.shownIconImage.getWidth()*0.25) #100
        shownIconLength = int(self.shownIconImage.getHeight()*0.25) #100
        resizedPreviewAWTimage = previewAWTimage.getScaledInstance(shownIconWidth, shownIconLength, 0)
        previewImageIcon = ImageIcon(resizedPreviewAWTimage, self.shownIconChannelTextDescription)
        return previewImageIcon

    def getShownIconImage(self):
        return self.shownIconImage

    def openColorChooser(self, event):
        #https://www.tutorialspoint.com/jython/jython_layout_management.htm
        self.colorChooserDialogBox = GenericDialogPlus("Channel color selector")
        #print("Layout: "+str(self.colorChooserDialogBox.getLayout()))
        channelLutColorSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        self.colorChooserDialogBox.add(self.channelLutColorSelector, channelLutColorSelectorConstraints)
        self.colorChooserDialogBox.showDialog();
        if self.colorChooserDialogBox.wasOKed():
            self.selectedPseudoColor = self.channelLutColorSelector.getColor()
            self.refreshPreviewIcon()

    def makeLutList(self):
        lutFilesList = ["---No_custom_LUT---"]

        imageJlutPath = IJ.getDirectory("luts") #https://www.codota.com/code/java/methods/ij.IJ/getDirectory
        #print("imageJlutPath: "+str(imageJlutPath))
        imageJlutEntries = os.listdir(imageJlutPath)
        for entry in imageJlutEntries:
            lutFilesList.append(entry)

        return JComboBox(lutFilesList)

    def openLutChooser(self, event):
        self.lutChooserDialogBox = GenericDialogPlus("Custom LUT selector")
        #print("Layout: "+str(self.lutChooserDialogBox.getLayout()))
        channelCustomLutSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        self.lutChooserDialogBox.add(self.lutDropdownList, channelCustomLutSelectorConstraints)
        self.lutChooserDialogBox.showDialog();
        if self.lutChooserDialogBox.wasOKed():
            self.selectedCustomLUT = self.lutDropdownList.getSelectedItem()
            self.refreshPreviewIcon()
            #return self.selectedCustomLUT

    def getPixelValuesFromSliders(self):
        vecteurSliders = self.pixelBoundaryValuesTunerDialogBox.getSliders()
        minHistogramPixelValues = []
        maxHistogramPixelValues = []
        for valueNumber in range(0,len(vecteurSliders)):
            if valueNumber%2 == 0:
                pixelValue = vecteurSliders[valueNumber].getValue()
                minHistogramPixelValues.append(pixelValue)
            if valueNumber%2 != 0:
                pixelValue = vecteurSliders[valueNumber].getValue()
                maxHistogramPixelValues.append(pixelValue)
        return minHistogramPixelValues, maxHistogramPixelValues

    def openPixelBoundaryValuesTuner(self, event):
        self.pixelBoundaryValuesTunerDialogBox = GenericDialogPlus("Min/Max pixel values")
        #print("Layout: "+str(self.pixelBoundaryValuesTunerDialogBox.getLayout()))
        #pixelBoundaryValuesTunerDialogBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        channelImageProcessor = self.channelImagePlus.getProcessor()
        bitDepth = channelImageProcessor.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
        minPixelBound = int(0) #Ne pas confondre getHistogramMin() avec getMin() (voir doc)
        maxPixelBound = int(2**bitDepth)-1 #Ne pas confondre getHistogramMax() avec getMax() (voir doc)
        self.pixelBoundaryValuesTunerDialogBox.addSlider("Pixel minimum histogramme", minPixelBound, maxPixelBound, self.selectedMinPixelValue)
        #self.pixelBoundaryValuesTunerDialogBox.addToSameRow() # The next item is appended next to the last one
        self.pixelBoundaryValuesTunerDialogBox.addSlider("Pixel maximum histogramme", minPixelBound, maxPixelBound, self.selectedMaxPixelValue)
        self.pixelBoundaryValuesTunerDialogBox.showDialog();
        if self.pixelBoundaryValuesTunerDialogBox.wasOKed():
            minHistogramPixelValues, maxHistogramPixelValues = self.getPixelValuesFromSliders()
            newMinPixelValue = minHistogramPixelValues[0]
            self.setSelectedMinPixelValue(newMinPixelValue)
            newMaxPixelValue = maxHistogramPixelValues[0]
            self.setSelectedMaxPixelValue(newMaxPixelValue)
            self.refreshPreviewIcon()

    def openInImageJ(self, event):
        print("Opening Channel "+str(self.channel_tuner_number)+" in Image/Fiji")
        self.channelImagePlus.show()

    def getSelectedPseudoColor(self):
        return self.selectedPseudoColor

    def getSelectedCustomLUT(self):
        return self.selectedCustomLUT

    def getSelectedMinPixelValue(self):
        return self.selectedMinPixelValue

    def getSelectedMaxPixelValue(self):
        return self.selectedMaxPixelValue

    def setSelectedPseudoColor(self, newColor):
        self.selectedPseudoColor = newColor

    def setSelectedCustomLUT(self,newLUT):
        self.selectedCustomLUT = newLUT

    def setSelectedMinPixelValue(self, newMinPixelValue):
        self.selectedMinPixelValue = newMinPixelValue

    def setSelectedMaxPixelValue(self, newMaxPixelValue):
        self.selectedMaxPixelValue = newMaxPixelValue

    def addToJavaWindow(self, javaWindow):
        gridBagConstraints = GridBagConstraints()
        gridBagConstraints.gridx = GridBagConstraints.RELATIVE
        gridBagConstraints.insets.left = 10;
        javaWindow.add(self.shownIconJLabel, gridBagConstraints)
        javaWindow.add(self.channelLutColorSelectorButton, gridBagConstraints)
        javaWindow.add(self.channelLutCustomLUTSelectorButton, gridBagConstraints)
        javaWindow.add(self.channelPixelBoundaryValuesTunerButton, gridBagConstraints)
        javaWindow.add(self.imageJDisplayButton, gridBagConstraints)

class ResultImagePreviewIcon:
    def __init__(self, channelTuners):

        self.channelTuners = channelTuners

        self.resultTextDescription = "Preview, Result Image"
        self.shownIconImage = self.makeShownResultImage()
        self.shownIcon = self.createIconFromImagePlus()
        self.shownIconJLabel = JLabel(self.shownIcon)
        #self.generalUpdatingButton = JButton("Update image", actionPerformed = self.refreshPreviewIcon)

    def makeShownResultImage(self):
        zProjectedRGBimages = []
        for channelTuner in self.channelTuners:
            shownPseudoColoredChannelImagePlus = channelTuner.getShownIconImage()
            zProjectedRGBimages.append(shownPseudoColoredChannelImagePlus)
        fusedChannelsImage = makeFusedChannelsImage(zProjectedRGBimages)
        return fusedChannelsImage

    def createIconFromImagePlus(self):
        previewAWTimage = self.shownIconImage.getImage()
        shownIconWidth = int(self.shownIconImage.getWidth()*0.25) #100
        shownIconLength = int(self.shownIconImage.getHeight()*0.25) #100
        resizedPreviewAWTimage = previewAWTimage.getScaledInstance(shownIconWidth, shownIconLength, 0)
        previewImageIcon = ImageIcon(resizedPreviewAWTimage, self.resultTextDescription)
        return previewImageIcon

    def setImageIcon(self, newIcon):
        self.shownIconJLabel.setIcon(newIcon)

    def refreshPreviewIcon(self):
        self.shownIconImage = self.makeShownResultImage()
        newShownIcon = self.createIconFromImagePlus()
        self.setImageIcon(newShownIcon)

    def getImageIcon(self):
        return self.shownIconJLabel

    def getShownIconImage(self):
        return self.shownIconImage

    def addToJavaWindow(self, javaWindow):
        #https://bbclone.developpez.com/fr/java/tutoriels/uiswing/gridbaglayout/?page=page_3
        gridBagConstraints = GridBagConstraints()
        gridBagConstraints.gridx = GridBagConstraints.RELATIVE
        gridBagConstraints.gridheight = 1 #valeur par défaut - peut s'étendre sur une seule ligne.
        gridBagConstraints.anchor = GridBagConstraints.LINE_START #ou BASELINE_LEADING mais pas WEST.
        gridBagConstraints.insets = Insets(10, 15, 0, 0) #Marge à gauche de 15 et marge au dessus de 10.
        #gridBagConstraints.insets.left = 10;
        javaWindow.add(self.shownIconJLabel, gridBagConstraints)
        #javaWindow.add(self.generalUpdatingButton, gridBagConstraints)

class MontageParametersTuner:
    def __init__(self, channelTunersArray, resultImageIcon):
        self.channelTunersArray = channelTunersArray
        self.resultImageIcon = resultImageIcon
        self.numberOfColumns = 3
        self.numberOfRows = 3
        self.preMontageImagesArray = self.makePreMontageImagesArray()
        #self.numberOfColumns, self.numberOfRows = self.autoAdjustMontageSize()
        self.digitsNumber = 0

        self.resultTextDescription = "Montage Image"
        self.shownIconImage = self.makeShownMontageImage()
        self.shownIcon = self.createIconFromImagePlus()
        self.shownIconJLabel = JLabel(self.shownIcon)

        self.montageParametersTunerButton = JButton("Nombre de lignes/colonnes", actionPerformed = self.openNumberRowColumnsWindow)

    def makePreMontageImagesArray(self):
        zProjectedRGBimages = []
        for channelTuner in self.channelTunersArray:
            channelImage = channelTuner.getShownIconImage()
            zProjectedRGBimages.append(channelImage)
        fusedChannelsImage = self.resultImageIcon.getShownIconImage()
        zDepthPreMontageImagesArray = makeArrayOfPreMontageImages(zProjectedRGBimages, fusedChannelsImage)
        return zDepthPreMontageImagesArray

    def makeShownMontageImage(self):
        montageImp = stackMontages(self.preMontageImagesArray, self.numberOfColumns, self.numberOfRows)
        return montageImp

    def createIconFromImagePlus(self):
        previewAWTimage = self.shownIconImage.getImage()
        shownIconWidth = int(self.shownIconImage.getWidth()*0.25) #100
        shownIconLength = int(self.shownIconImage.getHeight()*0.25) #100
        resizedPreviewAWTimage = previewAWTimage.getScaledInstance(shownIconWidth, shownIconLength, 0)
        previewImageIcon = ImageIcon(resizedPreviewAWTimage, self.resultTextDescription)
        return previewImageIcon

    def setImageIcon(self, newIcon):
        self.shownIconJLabel.setIcon(newIcon)

    def refreshPreviewIcon(self):
        self.preMontageImagesArray = self.makePreMontageImagesArray()
        #self.numberOfColumns, self.numberOfRows = self.autoAdjustMontageSize()
        self.shownIconImage = self.makeShownMontageImage()
        newShownIcon = self.createIconFromImagePlus()
        self.setImageIcon(newShownIcon)

    def getImageIcon(self):
        return self.shownIconJLabel

    def getShownIconImage(self):
        return self.shownIconImage

    def openNumberRowColumnsWindow(self, event):
        self.montageLinesColumnsBox = GenericDialogPlus("Entrer les valeurs")
        self.montageLinesColumnsBox.addNumericField("Nombre de lignes du montage", self.numberOfRows, self.digitsNumber)
        self.montageLinesColumnsBox.addNumericField("Nombre de colonnes du montage", self.numberOfColumns, self.digitsNumber)
        self.montageLinesColumnsBox.showDialog()
        if self.montageLinesColumnsBox.wasOKed():
            vecteurNumericFields = self.montageLinesColumnsBox.getNumericFields()
            inputNumberOfRows = vecteurNumericFields[0]
            numberOfRows = Integer.parseInt(inputNumberOfRows.getText())
            self.numberOfRows = int(numberOfRows)
            inputNumberOfColumns = vecteurNumericFields[1]
            numberOfColumns = Integer.parseInt(inputNumberOfColumns.getText())
            self.numberOfColumns = int(numberOfColumns)
            self.refreshPreviewIcon()

    def autoAdjustMontageSize(self): #Pas au point
        numberOfSlices = len(self.preMontageImagesArray)
        numberOfColumns = numberOfSlices
        numberOfRows = 1
        return numberOfColumns, numberOfRows

    def getNumberOfRows(self):
        return self.numberOfRows

    def getNumberOfColumns(self):
        return self.numberOfColumns

    def addToJavaWindow(self, javaWindow):
        gridBagConstraints = GridBagConstraints()
        gridBagConstraints.gridx = GridBagConstraints.RELATIVE
        gridBagConstraints.insets.left = 10;
        javaWindow.add(self.shownIconJLabel, gridBagConstraints)
        javaWindow.add(self.montageParametersTunerButton, gridBagConstraints)

#https://github.com/gatech-csl/jes/blob/master/jes/python/gui.py
# SliderListener
#
# Listener for the Slider widget.  eventHandler is called when the slider is
# moved - it is passed the current value of the slider.  Extends Swing's ChangeListener class.

class SliderListener(ChangeListener):
   """
   Event handler for sliders
   """

   def __init__(self, slider, eventFunction):
      """
      Points this listener to eventFunction when something happens
      """
      self.slider = slider   # remember which slider we are connected to, so we can poll it when a change happens
      self.eventFunction = eventFunction

   def stateChanged(self, event = None):
      """
      Call the eventFunction and return focus to the slider's parent display
      """
      sliderValue = self.slider.getValue()   # poll the slider
      self.eventFunction( sliderValue )      # and pass its changed value to the event handler
      self.slider.display.display.requestFocusInWindow()  # give focus to parent display

###-------------The listeners here are not used. I still have problems to understand how to use Java listeners with Jython

#https://github.com/gatech-csl/jes/blob/master/jes/python/gui.py
# DropDownListListener
#
# Listener for the DropDownList widget.  eventHandler is called when an item is
# selected - it is passed the item.  Extends Swing's ActionListener class.

class DropDownListListener(ActionListener):
   """
   Event handler for drop-down lists
   """

   def __init__(self, dropDownList, eventFunction):
      """
      Points this listener to eventFunction when something happens
      """
      self.dropDownList = dropDownList   # remember which dropDownList we are connected to, so we can poll it when a change happens
      self.eventFunction = eventFunction

   def actionPerformed(self, event = None):
      """
      Call the eventFunction and return focus to the dropDownList's parent display
      """
      item = self.dropDownList.getSelectedItem()   # poll the drop-down list
      self.eventFunction( item )                   # and pass it to the event handler
      self.dropDownList.display.display.requestFocusInWindow()  # give focus to parent display

class TuningSlider:
    def __init__(self, minBound, maxBound, defaultValue):
        self.minBound = minBound
        self.maxBound = maxBound
        self.defaultValue = defaultValue
        self.textFieldValue = str(defaultValue)
        self.sliderElement = JSlider(0, minBound, maxBound, defaultValue)
        self.textElement = JTextField(str(defaultValue))

    def getMin(self):
        return self.minBound

    def getMax(self):
        return self.maxBound

    def getValue(self):
        return self.defaultValue

    def setValue(self, newValue):
        self.defaultValue = newValue

    def updateItem(self, event, newValue):
        self.defaultValue = newValue
        self.textElement.setText(str(newValue))

    def addToJavaWindow(self, javaWindow):
        gridBagConstraints = GridBagConstraints()
        gridBagConstraints.gridx = GridBagConstraints.RELATIVE
        gridBagConstraints.insets.left = 10;
        javaWindow.add(self.sliderElement, gridBagConstraints)
        javaWindow.add(self.textElement, gridBagConstraints)



###############################################

def openMainDialogBox():
    # Create an instance of GenericDialogPlus
    mainDialogBox = GenericDialogPlus("Choix repertoire")
    mainDialogBox.addMessage("------------------------------------------")
    mainDialogBox.addDirectoryField("Choisir un repertoire-cible", "None")
    mainDialogBox.addMessage("------------------------------------------")

    booleanMetamorph = False

    mainDialogBox.addCheckbox("Fichiers metamorphiques (ND/TIFF)",booleanMetamorph)
    mainDialogBox.addMessage("On entend par fichier metamorphique un fichier de meta donnees accompagne de plusieurs fichiers image")
    mainDialogBox.addMessage("------------------------------------------")

    #Affichage de la boîte de dialogue
    mainDialogBox.showDialog();

    #Récupération choix
    folder = mainDialogBox.getNextString()
    vecteurChoix=mainDialogBox.getChoices()
    vecteurCheckBoxes=mainDialogBox.getCheckboxes()
    selectionBooleanMetamorphFiles = vecteurCheckBoxes[0]
    valeurSelectionBooleanMetamorphFiles = selectionBooleanMetamorphFiles.getState()

    #print(folder)
    if mainDialogBox.wasCanceled() == True:
        print("Cancel, End of Script")
        return None

    return folder, valeurSelectionBooleanMetamorphFiles

def openDialogBoxImageTuning(selectedPath, metamorphBoolean, separator):

    dumpSaveFilePath = str(folder)+separator+"dumps"
    if os.path.isdir(dumpSaveFilePath) == False:
        os.mkdir(dumpSaveFilePath)
    #imageListener = parameterModificationListener(firstImage)
    #firstImage.addImageListener(imageListener)

    imageSelector = ViewedImageSelector(selectedPath, metamorphBoolean)
    imageFilesList = imageSelector.getImageFilesList()
    imagesDictionary = imageSelector.getImageDictionary()
    valeurChoixZDepth = imageSelector.getSelectedZDepth()
    valeurChoixZProject = imageSelector.getSelectedZProjectMethodName()
    channelPseudoColorTuners = imageSelector.getChannelTunersArray()
    montageTuner = imageSelector.getMontageTuner()
    numberOfRows = montageTuner.getNumberOfRows()
    numberOfColumns = montageTuner.getNumberOfColumns()

    imageTuningDialogBox = JFrame("Modifications d'image",
        defaultCloseOperation = JFrame.EXIT_ON_CLOSE,
        size = (1000, 750)
    )
    imageTuningDialogBoxTabs = JTabbedPane()

    imageSelectorTab = JPanel(False)
    imageSelector.addToJavaWindow(imageSelectorTab)
    imageTuningDialogBoxTabs.addTab("Image Selector", imageSelectorTab)

    for channelNumber in range(0,len(channelPseudoColorTuners)):
        channelTitle = "Canal "+str(channelNumber+1)
        channelTunerTab = JPanel(False)
        channelPseudoColorTuners[channelNumber].addToJavaWindow(channelTunerTab)
        imageTuningDialogBoxTabs.addTab(channelTitle, channelTunerTab)

    resultMontageTuningTab = JPanel(False)
    montageTuner.addToJavaWindow(resultMontageTuningTab)
    imageTuningDialogBoxTabs.addTab("Montage tuning", resultMontageTuningTab)

    channelGlobalTab = JPanel(False)

    def makeMontagesPipeline(event):
        imageTuningDialogBox.dispose()
        impNumber = 0
        for imageFile in imageFilesList:
            #print("FILE: "+str(imageFile))
            #imagePlusFileInfo = imageFile.getFileInfo()
            #print("File_INFO: "+str(imagePlusFileInfo))
            #imagePlusFilePath = imagePlusFileInfo.getFilePath()
            impNumber+=1
            serieNumber = 0
            for serie in imagesDictionary[imageFile]:
                serieNumber+=1
                imagePlusFilePath = serie.getTitle()
                print(imagePlusFilePath)
                montageImp = makeJob(serie, valeurChoixZProject, numberOfColumns, numberOfRows, channelPseudoColorTuners)
                #montageImp.show()
                fileName = (imagePlusFilePath.split(separator)[-1]).split(".")[0]
                dumpFileName = str(valeurChoixZProject)+"_"+str(fileName)+"_"+str(impNumber)+"_"+str(serieNumber)
                print(dumpFileName)
                saveFileImage(montageImp, imagePlusFilePath, dumpSaveFilePath, dumpFileName, separator)
        print("End")

    def shutDown(event):
        imageTuningDialogBox.dispose()
        print("End")

    sendValuesButton = JButton("Launch selected parameters on all images in directory", actionPerformed = makeMontagesPipeline)
    cancelButton = JButton("Quit plugin", actionPerformed = shutDown)
    channelGlobalTab.add(sendValuesButton)
    channelGlobalTab.add(cancelButton)
    imageTuningDialogBoxTabs.addTab("Global", channelGlobalTab)

    imageTuningDialogBox.add(imageTuningDialogBoxTabs)

    #Affichage de la boîte de dialogue
    imageTuningDialogBox.visible = True

def makeBluePixel(integerGrayLevel, bitDepth):
    if integerGrayLevel > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
        integerGrayLevel = (2**bitDepth)-1
    if bitDepth == 8:
        integer8bitGrayValue = integerGrayLevel
    if bitDepth == 16:
        integer16bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer16bitGrayValue >> 8 #8 en réalité, >> 4 en corrigé pour 12bit
    if bitDepth == 32:
        integer32bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer32bitGrayValue >> 16
    pixelBlueValue = (integer8bitGrayValue)
    colouredLevel = pixelBlueValue
    return colouredLevel

def makeGreenPixel(integerGrayLevel, bitDepth):
    if integerGrayLevel > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
        integerGrayLevel = (2**bitDepth)-1
    if bitDepth == 8:
        integer8bitGrayValue = integerGrayLevel
    if bitDepth == 16:
        integer16bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer16bitGrayValue >> 8 #8 en réalité, >> 4 en corrigé pour 12bit
    if bitDepth == 32:
        integer32bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer32bitGrayValue >> 16
    pixelGreenValue = (integer8bitGrayValue << 8)
    colouredLevel = pixelGreenValue
    return colouredLevel

def makeRedPixel(integerGrayLevel, bitDepth):
    if integerGrayLevel > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
        integerGrayLevel = (2**bitDepth)-1
    if bitDepth == 8:
        integer8bitGrayValue = integerGrayLevel
    if bitDepth == 16:
        integer16bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer16bitGrayValue >> 8 #8 en réalité, >> 4 en corrigé pour 12bit
    if bitDepth == 32:
        integer32bitGrayValue = integerGrayLevel
        integer8bitGrayValue = integer32bitGrayValue >> 16
    pixelRedValue = (integer8bitGrayValue << 16)
    colouredLevel = pixelRedValue
    return colouredLevel

    #https://forum.image.sc/t/gamma-adjustment-in-brightness-contrast-window/768/2
    #https://forum.image.sc/t/how-to-have-a-batch-of-images-with-the-same-brightness-and-contrast/3914/2

def processorsTuningPipeline(channelImageProcessor, newPseudoColoredChannelImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, selectedPseudoColor, selectedLUT, channelNumber, selectedZDepth, selectedZProjectMethodName):
    lutPath = IJ.getDirectory("luts")
    #print(str(lutPath))
    #channelImageProcessor = channelImagePlus.getProcessor() #à revoir
    channelImageProcessor.setMinAndMax(valeurPixelMinHistogram, valeurPixelMaxHistogram) #Ne pas confondre setHistogramRange() avec setMinAndMax() (voir doc)
    newPseudoColoredChannelImageProcessor = newPseudoColoredChannelImagePlus.getProcessor()
    imageHeight = newPseudoColoredChannelImageProcessor.getHeight()
    imageWidth = newPseudoColoredChannelImageProcessor.getWidth()
    bitDepth = newPseudoColoredChannelImageProcessor.getBitDepth()
    originalImageBitDepth = channelImageProcessor.getBitDepth()
    leveledBitDepth = 8
    #leveledBitDepth = int(originalImageBitDepth)
    #print("leveledBitDepth: "+str(leveledBitDepth))
    maxLevelValue = int(channelImageProcessor.getMax())
    minLevelValue = int(channelImageProcessor.getMin())

    imageName = "Channel "+str(channelNumber)+" - Z-Depth: "+str(selectedZDepth)+" - Z-Project: "+str(selectedZProjectMethodName)+" - Min value: "+str(minLevelValue)+", Max value: "+str(maxLevelValue)+", Color: "+str(selectedPseudoColor)+", LUT: "+str(selectedLUT)
    #print(imageName)
    newPseudoColoredChannelImagePlus.setTitle(String(imageName))
    if selectedLUT != "---No_custom_LUT---":
        customLUT = LutLoader.openLut(lutPath+selectedLUT)
        customLUTbytes = customLUT.getBytes()
        #print(customLUTbytes)
        #print(len(customLUTbytes))

        def divide_chunks(l, n): #https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
            # looping till length l
            for i in range(0, len(l), n):
                yield l[i:i + n]

        maxGrayValue = int((2**leveledBitDepth)-1)
        customLUTbytes_ordered_by_color = list(divide_chunks(customLUTbytes, 256)) #LUT: 768 valeurs = 256 x 3
        customLUT_redValues = customLUTbytes_ordered_by_color[0]
        customLUT_greenValues = customLUTbytes_ordered_by_color[1]
        customLUT_blueValues = customLUTbytes_ordered_by_color[2]
        for indice in range(imageWidth*imageHeight):
            integerGrayLevel = channelImageProcessor.get(indice)
            leveledGrayValue = int(integerGrayLevel*maxGrayValue/(maxLevelValue-minLevelValue))
            leveledBlueValue = customLUT_blueValues[leveledGrayValue]
            leveledGreenValue = customLUT_greenValues[leveledGrayValue]
            leveledRedValue = customLUT_redValues[leveledGrayValue]
            pixelBlueValue = makeBluePixel(leveledBlueValue, leveledBitDepth)
            pixelGreenValue = makeGreenPixel(leveledGreenValue, leveledBitDepth)
            pixelRedValue = makeRedPixel(leveledRedValue, leveledBitDepth)
            colouredPixelValue = pixelBlueValue + pixelGreenValue + pixelRedValue
            colouredPixelValue = int(colouredPixelValue)
            newPseudoColoredChannelImageProcessor.set(indice, colouredPixelValue)

    if selectedLUT == "---No_custom_LUT---":
        #createLutFromColor(java.awt.Color color) - Creates a color LUT from a Color.
        maxRedValue = selectedPseudoColor.getRed()
        maxGreenValue = selectedPseudoColor.getGreen()
        maxBlueValue = selectedPseudoColor.getBlue()
        for indice in range(imageWidth*imageHeight):
            integerGrayLevel = channelImageProcessor.get(indice)
            leveledBlueValue = int(integerGrayLevel*maxBlueValue/(maxLevelValue-minLevelValue))
            leveledGreenValue = int(integerGrayLevel*maxGreenValue/(maxLevelValue-minLevelValue))
            leveledRedValue = int(integerGrayLevel*maxRedValue/(maxLevelValue-minLevelValue))
            pixelBlueValue = makeBluePixel(leveledBlueValue, leveledBitDepth)
            pixelGreenValue = makeGreenPixel(leveledGreenValue, leveledBitDepth)
            pixelRedValue = makeRedPixel(leveledRedValue, leveledBitDepth)
            colouredPixelValue = pixelBlueValue + pixelGreenValue + pixelRedValue
            colouredPixelValue = int(colouredPixelValue)
            newPseudoColoredChannelImageProcessor.set(indice, colouredPixelValue)

    return newPseudoColoredChannelImageProcessor

def makeChannelTuningPipeline(channelImagePlus, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, selectedZProjectMethodName):
    zDepthForChannel = channelImagePlus.getNSlices() #Profondeur Z
    imageWidth = channelImagePlus.getWidth(); #Largeur de l'image
    imageHeight = channelImagePlus.getHeight(); #Hauteur de l'image
    bitDepth = channelImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    channelStackedImages = channelImagePlus.getStack()
    newPseudoColoredChannelStack = ImageStack(imageWidth, imageHeight)

    if selectedLUT == "---No_custom_LUT---":
        newPseudoColoredChannelImageTitle = "LUTted "+str(selectedPseudoColor)+", Channel "+str(channelNumber)
    if selectedLUT != "---No_custom_LUT---":
        newPseudoColoredChannelImageTitle = "LUTted "+str(selectedLUT)+", Channel "+str(channelNumber)

    for zNumber in range(0, zDepthForChannel):
        zImageProcessor = channelStackedImages.getProcessor(zNumber+1)
        newPseudoColoredChannelZImagePlus = IJ.createImage(str(newPseudoColoredChannelImageTitle)+", Z-Depth "+str(zNumber+1), "RGB Black", imageWidth, imageHeight, 1)
        newPseudoColoredChannelZImageProcessor = processorsTuningPipeline(zImageProcessor, newPseudoColoredChannelZImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, selectedPseudoColor, selectedLUT, channelNumber, zNumber, selectedZProjectMethodName)
        newPseudoColoredChannelZImagePlus.setProcessor(newPseudoColoredChannelZImageProcessor)
        newPseudoColoredChannelStack.addSlice(newPseudoColoredChannelZImageProcessor)
    newPseudoColoredChannelImagePlus = ImagePlus(String(newPseudoColoredChannelImageTitle), newPseudoColoredChannelStack)
    return newPseudoColoredChannelImagePlus

def median(listOfNumbers):
	listOfNumbers.sort()
	middle = len(listOfNumbers)/2
	if ((len(listOfNumbers) & 1) == 0):
		return int((listOfNumbers[middle-1] + listOfNumbers[middle])/2)
	else:
		return listOfNumbers[middle]

def makeZProjectOnSingleChannel(channelImage, methodName):
    ####---MY Z-PROJECT ALGORITHM IS HERE---######
    imageWidth = channelImage.getWidth()
    imageHeight = channelImage.getHeight()
    bitDepth = channelImage.getBitDepth()
    if bitDepth == 8:
        newZProjectChannelImage = IJ.createImage("Z-Project "+str(methodName), "8-bit Black", imageWidth, imageHeight, 1)
    if bitDepth == 16:
        newZProjectChannelImage = IJ.createImage("Z-Project "+str(methodName), "16-bit Black", imageWidth, imageHeight, 1)
    if bitDepth == 24: #RGB
        newZProjectChannelImage = IJ.createImage("Z-Project "+str(methodName), "RGB Black", imageWidth, imageHeight, 1)
    if bitDepth == 32:
        newZProjectChannelImage = IJ.createImage("Z-Project "+str(methodName), "32-bit Black", imageWidth, imageHeight, 1)
    newZProjectChannelImageProcessor = newZProjectChannelImage.getProcessor()
    channelStackofZs = channelImage.getStack()
    zDepthMax = channelImage.getNSlices()
    for indice in range(imageWidth*imageHeight):
        pixelValuesForEachChannel = []
        globalPixelValue = 0
        for zNumber in range(0, zDepthMax):
            zDepthProcessor = channelStackofZs.getProcessor(zNumber+1)
            zDepthPixelValue = zDepthProcessor.get(indice)
            pixelValuesForEachChannel.append(zDepthPixelValue)

        if methodName == "max":
            globalPixelValue = max(pixelValuesForEachChannel)
        if methodName == "min":
            globalPixelValue = min(pixelValuesForEachChannel)
        if methodName == "sum":
            globalPixelValue = sum(pixelValuesForEachChannel)
        if methodName == "average":
            globalPixelValue = int(sum(pixelValuesForEachChannel)/len(pixelValuesForEachChannel))
        if methodName == "median":
            globalPixelValue = int(median(pixelValuesForEachChannel))

        if globalPixelValue > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
            globalPixelValue = (2**bitDepth)-1

        newZProjectChannelImageProcessor.set(indice, globalPixelValue)
    return newZProjectChannelImage

def makeZProject(imagePlus, methodName):
    arrayOfChannels = separateByChannels(imagePlus)
    arrayOfZProjectedChannels = []
    numberOfChannels = len(arrayOfChannels)
    for channelImage in arrayOfChannels:
        newZProjectChannelImage = makeZProjectOnSingleChannel(channelImage, methodName)
        arrayOfZProjectedChannels.append(newZProjectChannelImage)
    return arrayOfZProjectedChannels

def makeImageJZProject(imagePlus, methodName):
    #https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/plugin/ZProjector.java
    #https://imagej.nih.gov/ij/developer/api/ij/plugin/ZProjector.html
    #https://imagej.net/Z-functions
    zProjectImageStack = ZProjector.run(imagePlus, methodName) #Retourne un stack de canaux. Chaque canal correspond à la projection sur Z. Ne donne qu'une superposition des canaux pour une image d'une seule profondeur.
    zProjectImagePlus = ImagePlus("Z-Project "+str(methodName), zProjectImageStack)
    zProjectChannels = separateByChannels(zProjectImagePlus)
    return zProjectChannels


def makeJob(imagePlus, selectedZProjectMethodName, numberOfColumns, numberOfRows, channelPseudoColorTuners):
    if selectedZProjectMethodName == "---No_Z-Project---":
        arrayOfChannels = separateByChannels(imagePlus)
        zProjectChannels = arrayOfChannels
    else:
        zProjectChannels = makeZProject(imagePlus, selectedZProjectMethodName)
        #zProjectChannels = makeImageJZProject(imagePlus, selectedZProjectMethodName)

    channelNumber = 0

    zProjectedRGBimages = []
    for zProjectChannelImage in zProjectChannels:
        channelPseudoColorTuner = channelPseudoColorTuners[channelNumber]
        selectedPseudoColor = channelPseudoColorTuner.getSelectedPseudoColor()
        selectedLUT = channelPseudoColorTuner.getSelectedCustomLUT()
        valeurPixelMinHistogram = channelPseudoColorTuner.getSelectedMinPixelValue()
        valeurPixelMaxHistogram = channelPseudoColorTuner.getSelectedMaxPixelValue()
        newPseudoColoredChannelImagePlus = makeChannelTuningPipeline(zProjectChannelImage, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, selectedZProjectMethodName)
        zProjectedRGBimages.append(newPseudoColoredChannelImagePlus)
        channelNumber+=1

    fusedChannelsImage = makeFusedChannelsImage(zProjectedRGBimages)
    zDepthPreMontageImagesArray = makeArrayOfPreMontageImages(zProjectedRGBimages, fusedChannelsImage)
    montageImp = stackMontages(zDepthPreMontageImagesArray, numberOfColumns, numberOfRows)
    return montageImp

def makeFusedChannelsImage(arrayOfImages):
    #print("Nb images pour fusion: "+str(len(arrayOfImages)))
    imageWidth = arrayOfImages[0].getWidth()
    imageHeight = arrayOfImages[0].getHeight()
    bitDepth = arrayOfImages[0].getBitDepth()
    zMaxDepth = arrayOfImages[0].getNSlices()

    fusedImagesStack = ImageStack(imageWidth, imageHeight)
    #Additionner les canaux ici
    #print("Make Fused Image...")
    for zNumber in range(0, zMaxDepth):
        if bitDepth == 8:
            newFusedImage = IJ.createImage("Fused image, Z-Depth "+str(zNumber+1), "8-bit Black", imageWidth, imageHeight, 1)
        if bitDepth == 16:
            newFusedImage = IJ.createImage("Fused image, Z-Depth "+str(zNumber+1), "16-bit Black", imageWidth, imageHeight, 1)
        if bitDepth == 24: #RGB
            newFusedImage = IJ.createImage("Fused image, Z-Depth "+str(zNumber+1), "RGB Black", imageWidth, imageHeight, 1)
        if bitDepth == 32:
            newFusedImage = IJ.createImage("Fused image, Z-Depth "+str(zNumber+1), "32-bit Black", imageWidth, imageHeight, 1)

        newFusedImageProcessor = newFusedImage.getProcessor()
        for indice in range(imageWidth*imageHeight):
            pixelSumValue = 0
            numImage = 0
            for channelImage in arrayOfImages:
                channelStack = channelImage.getStack()
                zNumberImageProcessor = channelStack.getProcessor(zNumber+1)
                imagePixelValue = zNumberImageProcessor.get(indice)
                pixelSumValue = pixelSumValue + imagePixelValue
            if pixelSumValue > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
                pixelSumValue = (2**bitDepth)-1
            newFusedImageProcessor.set(indice, pixelSumValue)
        fusedImagesStack.addSlice(newFusedImageProcessor)
    fusedImagesImagePlus = ImagePlus("Fused Image", fusedImagesStack)
    #fusedImagesImagePlus.show()
    return fusedImagesImagePlus

def separateByChannels(mainImageStackImp):
    mainProcessor = mainImageStackImp.getProcessor()
    numberOfChannels = mainImageStackImp.getNChannels() #Nombre de canaux
    print("numberOfChannels: "+str(numberOfChannels))
    zDepthByChannel = mainImageStackImp.getNSlices() #Profondeur Z
    print("zDepthByChannel: "+str(zDepthByChannel))
    imageWidth = mainImageStackImp.getWidth(); #Largeur de l'image
    imageHeight = mainImageStackImp.getHeight(); #Hauteur de l'image
    bitDepth = mainImageStackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    stackedImages = mainImageStackImp.getStack()
    #totalNumberOfImages = mainImageStackImp.getStackSize() #Profondeur Z * Nombre de canaux
    totalNumberOfImages = stackedImages.getSize() #Profondeur Z * Nombre de canaux
    print("totalNumberOfImages: "+str(totalNumberOfImages))

    arrayOfChannels = []
    for channelNumber in range(0,numberOfChannels):
        channelStack = ImageStack(imageWidth, imageHeight)
        zDepthNumber = 1
        for imageNumber in range(channelNumber, totalNumberOfImages, numberOfChannels):
            sliceTitle = stackedImages.getSliceLabel(imageNumber+1)
            sliceProcessor = stackedImages.getProcessor(imageNumber+1)
            channelStack.addSlice(sliceTitle, sliceProcessor)
            zDepthNumber+=1
        channelTitle = String("Channel "+str(channelNumber))
        channelImagePlus = ImagePlus(channelTitle, channelStack)
        arrayOfChannels.append(channelImagePlus)
    return arrayOfChannels

def makeArrayOfPreMontageImages(arrayOfChannels, fusedImage):
    zDepthPreMontageImages = []
    fusedImageStack = fusedImage.getStack()
    imageWidth = fusedImage.getWidth()
    imageHeight = fusedImage.getHeight()
    maxZDepth = fusedImage.getNSlices()
    for zDepth in range(0, maxZDepth):
        newOneZDepthStack = ImageStack(imageWidth, imageHeight)
        for channelImage in arrayOfChannels:
            channelStack = channelImage.getStack()
            selectedSliceProcessor = channelStack.getProcessor(zDepth+1)
            newOneZDepthStack.addSlice(selectedSliceProcessor)
        selectedFusedSliceProcessor = fusedImageStack.getProcessor(zDepth+1)
        newOneZDepthStack.addSlice(selectedFusedSliceProcessor)
        newOneZDepthImage = ImagePlus("Pre-Montage, Z-Depth: "+str(zDepth+1), newOneZDepthStack)
        zDepthPreMontageImages.append(newOneZDepthImage)
    return zDepthPreMontageImages

def stackMontages(arrayOfDisplayableStacks, numberOfColumns, numberOfRows):
    depthStack = ImageStack()
    for stackImp in arrayOfDisplayableStacks:
        newMontageImage, montageWidth, montageHeight = makeMontage(stackImp, numberOfColumns, numberOfRows)
        newMontageImageProcessor = newMontageImage.getProcessor()
        depthStack.addSlice(newMontageImageProcessor)
    depthStackImp = ImagePlus("Montage Z-Project", depthStack)
    return depthStackImp

def makeMontage(stackImp, numberOfColumns, numberOfRows):
    #IJ.run(stackImp, "Make Montage...", "columns=2 rows=2 scale=0.50"); #Ne retourne rien -> Useless
    #stackImp.show()
    stack = stackImp.getStack()
    bitDepth = stackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    imageWidth = stackImp.getWidth(); #Largeur de l'image
    imageHeight = stackImp.getHeight(); #Hauteur de l'image
    numberOfSlices = stackImp.getNSlices() #Nombre d'images du stack
    montageWidth = imageWidth*int(numberOfColumns)
    montageHeight = imageHeight*int(numberOfRows)

    if bitDepth == 8:
        newMontageImage = IJ.createImage("Montage", "8-bit Black", montageWidth, montageHeight, 1)
    if bitDepth == 16:
        newMontageImage = IJ.createImage("Montage", "16-bit Black", montageWidth, montageHeight, 1)
    if bitDepth == 24:
        newMontageImage = IJ.createImage("Montage", "RGB Black", montageWidth, montageHeight, 1)
    if bitDepth == 32:
        newMontageImage = IJ.createImage("Montage", "32-bit Black", montageWidth, montageHeight, 1)

    newMontageImageProcessor = newMontageImage.getProcessor()

    yMontage = 0
    xMontage = 0
    newXOrigin = 0
    newYOrigin = 0
    for imageNumber in range(0,numberOfSlices):
        imageProcessor = stack.getProcessor(imageNumber+1)
        for y in range(imageHeight):
            yMontage = (newYOrigin)+y
            for x in range(imageWidth):
                xMontage = (newXOrigin)+x
                #pixel = imageProcessor.getPixel(x,y)
                pixel = imageProcessor.get(x,y)
                #newMontageImageProcessor.putPixel(xMontage,yMontage,pixel)
                newMontageImageProcessor.set(xMontage,yMontage,pixel)
        if newXOrigin*newYOrigin >= montageWidth*montageHeight:
            break
        if newXOrigin < montageWidth:# and newXOrigin != 0:
            newXOrigin = newXOrigin+imageWidth
            newYOrigin = newYOrigin
        if newXOrigin == montageWidth:
            newXOrigin = 0
            newYOrigin = newYOrigin+imageHeight


    newMontageImage.setProcessor(newMontageImageProcessor)
    return newMontageImage, montageWidth, montageHeight

def saveFileImage(imagePlus, imagePlusFilePath, dumpSaveFilePath, dumpFileName, separator):
    print("PATH: "+str(imagePlusFilePath))
    fileSaver = FileSaver(imagePlus)
    imageName = imagePlus.getTitle()
    #File.makeDirectory(dumpDirectory)
    dumpFileString = str(dumpSaveFilePath)+str(separator)+str(imageName)+"_"+str(dumpFileName)
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

IJ.log('\\Clear') #efface le contenu de la console

#frame = Frame()
#dialog = GenericDialog("Z-Project")
#button = Button ("Ouvrir fichier")
#button.addActionListener(imageSelectionListener())
#dialog.add(button)
#f.pack()
#f.setVisible(1)

folder, valeurSelectionBooleanMetamorphFiles = openMainDialogBox()
your_os = System.getProperty("os.name");
print(your_os)
if your_os == "Windows" or your_os == "Windows 10":
    separator = "\\"
elif your_os == "Unix" or your_os == "Linux" or your_os == "Mac":
    separator = "/"

openDialogBoxImageTuning(folder, valeurSelectionBooleanMetamorphFiles, separator)
