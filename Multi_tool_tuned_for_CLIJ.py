#-*- coding: utf-8 -*-

import os, sys
from sys import path
import java, jarray, array
#from jarray import array
import math
from java.io import File
from java.lang import System, Integer, Float, String
from java.awt import Frame, Dialog, Button, Color, GridBagLayout, GridBagConstraints, Insets
from java.awt.event import ActionEvent, ActionListener, MouseAdapter, AdjustmentListener
from javax.swing import JDialog, JFrame, JPanel, JTabbedPane, JScrollPane, JLabel, JButton, JTextField, JSlider, JColorChooser, JComboBox, ImageIcon
from javax.swing.colorchooser import AbstractColorChooserPanel
from javax.swing.event import ChangeEvent, ChangeListener
from ij import IJ, ImageStack, ImagePlus, CompositeImage, ImageListener, VirtualStack, WindowManager
from ij.gui import GenericDialog
from ij.io import OpenDialog, FileSaver
from ij.measure import Calibration
from ij.plugin import LutLoader, ZProjector, HyperStackConverter, MontageMaker, RGBStackMerge
from ij.process import ImageProcessor, FloatProcessor, ShortProcessor, ByteProcessor, LUT
from fiji.util.gui import GenericDialogPlus
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.plugins.util import BFVirtualStack
from loci.formats import ImageReader, ChannelSeparator
from loci.formats.in import MetamorphReader


class ViewedImageSelector: #Détermine image, série, Z sélectionnés.
    """
    Détermine image, série, Z sélectionnés. Instancié dès le lancement du plugin.
    Dès l'instanciation, instancie un dictionnaire des images observées dans l'interface.
    Un fichier image (le premier généralement) est chargé par défaut dans le dico (avec toutes ses séries).
    Lors d'un changement de fichier, le nouveau fichier est ajouté dans le dico.
    Les dimensions des images de preview sont aussi gérées ici (resize)
    """
    def __init__(self, selectedPath, metamorphBoolean, valeurChoixOperation, valeurSelectionBooleanCLIJ, clij2_instance, separator):
        self.selectedPath = selectedPath
        self.pathSeparator = separator
        self.selectedSavePath = str(self.selectedPath)+str(self.pathSeparator)+"dumps"
        self.metamorphBoolean = metamorphBoolean
        self.selectedOperation = valeurChoixOperation
        self.valeurSelectionBooleanCLIJ = valeurSelectionBooleanCLIJ
        self.clij2_instance = clij2_instance
        self.listOfDirectoryImageFiles = self.getImpList()
        self.imageFilesDropDownList = self.makeImageFileDropdownList()
        self.zProjectDropdownList = self.makeZProjectDropdownList()

        self.previewRedimensionCoef = 0.125
        self.selectedImageFileName = str(self.listOfDirectoryImageFiles[0])
        self.selectedSerie = 1
        self.imageDictionary = self.initializeDictionaryOfLoadedImages()
        self.selectedImageSerie = self.imageDictionary[str(self.selectedImageFileName)]["Serie "+str(self.selectedSerie)]

        self.currentlyShownResultImage = self.extractShownResultImage()
        self.shownIconResultTextDescription = "Result Image"

    def getSeparator(self):
        return self.pathSeparator

    def getImpList(self):
        #Voir https://forum.image.sc/t/cannot-import-nd-files-via-fiji-macro/26150/3
        metamorphList = []
        fileList = os.listdir(self.selectedPath)
        fileOnlyList = []
        for item in fileList:
            if os.path.isfile(str(self.selectedPath)+str(self.pathSeparator)+str(item)) == True:
                fileOnlyList.append(str(item))

        for file in fileOnlyList:
            extension = file.split('.').pop() #Array.pop(). Pratique pour faire une fonction getExtension()
            if extension == "nd":
                metamorphList.append(file)
        if self.metamorphBoolean == True:
            return metamorphList
        if self.metamorphBoolean == False:
            return fileOnlyList

    def getListOfImageFiles(self):
        return self.listOfDirectoryImageFiles

    def initializeDictionaryOfLoadedImages(self):
        dictionaryOfLoadedImages = {}
        dictionaryOfLoadedImages[str(self.selectedImageFileName)] = self.openImageFile(self.selectedImageFileName)
        return dictionaryOfLoadedImages

    def makeZProjectDropdownList(self):
        choixZProject = ["---No_Z-Project---", "max", "min", "sum", "average", "median", "sd"]
        return JComboBox(choixZProject)

    def openImageFile(self, imageFileName):
        #IJ.log(imageFile)
        imageFilePath = str(self.selectedPath)+str(self.pathSeparator)+str(imageFileName)
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
        seriesOfImageFile = {}
        options = ImporterOptions()
        options.setId(imageId)

        for numberSerie in range(seriesCount):
            options.setSeriesOn(numberSerie,True); #Pour LIF - compter les séries - https://gist.github.com/ctrueden/6282856
            imageStackImps = BF.openImagePlus(options);
            #print imageStackImps
            mainImageStackImp = imageStackImps[-1] #0
            mainImageStackImp.setTitle(str(imageFileName)+"_"+str(numberSerie))
            print("Making dictionary of "+mainImageStackImp.getTitle())
            seriesOfImageFile["Serie "+str(numberSerie+1)] = {}
            seriesOfImageFile["Serie "+str(numberSerie+1)]["ImagePlus"] = mainImageStackImp
            seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"] = {}
            seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["imageCalibration"] = mainImageStackImp.getCalibration()
            seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["selectedZDepth"] = 1
            seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["selectedZProjectMethodName"] = "---No_Z-Project---"
            seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["ChannelTunersArray"] = self.createChannelTunersArray(seriesOfImageFile["Serie "+str(numberSerie+1)]["ImagePlus"], seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["selectedZDepth"], seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["selectedZProjectMethodName"])
            seriesOfImageFile["Serie "+str(numberSerie+1)]["ResultImagesDictionary"] = self.makeDictionaryOfCurrentImages(seriesOfImageFile["Serie "+str(numberSerie+1)]["GlobalSettings"]["ChannelTunersArray"])
            seriesOfImageFile["Serie "+str(numberSerie+1)]["ResultTuner"] = self.createResultTuner(seriesOfImageFile["Serie "+str(numberSerie+1)])
            print("Finished making dictionary of "+mainImageStackImp.getTitle())
        return seriesOfImageFile

    def createChannelTunersArray(self, selectedImagePlus, defaultSelectedZDepth, defaultSelectedZProjectMethodName):
        print("Creating channel tuners")
        redimensionCoef = self.previewRedimensionCoef
        resizedImagePlusForIcons = selectedImagePlus.resize(int(redimensionCoef*selectedImagePlus.getWidth()), int(redimensionCoef*selectedImagePlus.getHeight()), "bilinear") # "bilinear" or "none"
        selectedImageAndSerieArrayOfChannels = separateByChannels(resizedImagePlusForIcons)
        channelTunersArray = []
        for channelNumber in range(0,len(selectedImageAndSerieArrayOfChannels)):
            channelImage = selectedImageAndSerieArrayOfChannels[channelNumber]
            channelTuner = ChannelTuner(channelImage, channelNumber, defaultSelectedZDepth, defaultSelectedZProjectMethodName, self.selectedOperation, self.valeurSelectionBooleanCLIJ, self.clij2_instance)
            channelTunersArray.append(channelTuner)
        print("Finished creating channel tuners")
        return channelTunersArray

    def makeDictionaryOfCurrentImages(self, channelTuners):
        print("Making initial fused images")
        zProjectedTunedImages = []
        for channelTuner in channelTuners:
            pseudoColoredChannelImagePlus = channelTuner.getImagePlus()
            zProjectedTunedImages.append(pseudoColoredChannelImagePlus)

        if self.selectedOperation == "Make Montage":
            fusedChannelsImage = makeFusedChannelsRedGreenBlueImage(zProjectedTunedImages)
        if self.selectedOperation == "Make Composite":
            fusedChannelsImage = makeFusedChannelsCompositeImage(zProjectedTunedImages)

        print("Making initial dictionary of viewable images")
        dictionaryOfCurrentImages = makeDictionaryOfViewableImages(zProjectedTunedImages, fusedChannelsImage)
        return dictionaryOfCurrentImages

    def createResultTuner(self, selectedImageSerie):
        if self.selectedOperation == "Make Montage":
            resultTuner = MontageTuner(selectedImageSerie, self.valeurSelectionBooleanCLIJ, self.clij2_instance)
        if self.selectedOperation == "Make Composite":
            resultTuner = CompositeTuner(selectedImageSerie, self.valeurSelectionBooleanCLIJ, self.clij2_instance)
        return resultTuner

    def refreshDictionaryOfCurrentImages(self): #Essayer d'ajouter un booleen dans les ChannelTuner pour détecter les changements
        zProjectedTunedImages = []
        for channelTuner in self.selectedImageSerie["GlobalSettings"]["ChannelTunersArray"]:
            #if channelTuner.getTuningStateBoolean() == True:
            #channelTuner.refreshImagePlus()
            pseudoColoredChannelImagePlus = channelTuner.getImagePlus()
            zProjectedTunedImages.append(pseudoColoredChannelImagePlus)
        if self.selectedOperation == "Make Montage":
            fusedChannelsImage = makeFusedChannelsRedGreenBlueImage(zProjectedTunedImages)
        if self.selectedOperation == "Make Composite":
            fusedChannelsImage = makeFusedChannelsCompositeImage(zProjectedTunedImages)

        for channelImage in zProjectedTunedImages:
            channelImageTitle = channelImage.getTitle()
            self.selectedImageSerie["ResultImagesDictionary"][str(channelImageTitle)] = channelImage
        fusedImageTitle = fusedChannelsImage.getTitle()
        self.selectedImageSerie["ResultImagesDictionary"][str(fusedImageTitle)] = fusedChannelsImage

    def extractShownResultImage(self):
        currentResultImage = self.selectedImageSerie["ResultImagesDictionary"]["Fused Image"]
        stackedResultImage = currentResultImage.getStack()
        zProjectMethodName = self.selectedImageSerie["GlobalSettings"]["selectedZProjectMethodName"]
        if zProjectMethodName == "---No_Z-Project---":
            zNumber = self.selectedImageSerie["GlobalSettings"]["selectedZDepth"]
        if zProjectMethodName != "---No_Z-Project---":
            zNumber = 1
        shownImageProcessor = stackedResultImage.getProcessor(zNumber)
        shownImage = IJ.createImage("Z-Project "+str(zProjectMethodName)+"Z-Number: "+str(zNumber), "RGB Black", currentResultImage.getWidth(), currentResultImage.getHeight(), 1)
        shownImage.setProcessor(shownImageProcessor)
        return shownImage

    def getShownIconImage(self):
        return self.currentlyShownResultImage

    def detectChangeInChannelTuners(self): #Pas au point
        booleanChangeInChannelTuners = False
        for channelTuner in self.selectedImageSerie["GlobalSettings"]["ChannelTunersArray"]:
            #print(channelTuner.getTuningStateBoolean())
            if channelTuner.getTuningStateBoolean() == True:
                booleanChangeInChannelTuners = True
                break
        return booleanChangeInChannelTuners

    def refreshShownIconImage(self): #Ajouter référence au booléen ici
        booleanChangeInChannelTuners = self.detectChangeInChannelTuners()
        #if booleanChangeInChannelTuners == True:
        self.refreshDictionaryOfCurrentImages()
        newShownIconImage = self.extractShownResultImage()
        self.currentlyShownResultImage = newShownIconImage

    def refreshAllCurrentShownImages(self):
        currentlySelectedImageSerie = self.getCurrentlySelectedImageSerie()
        #Problème sélection Z-Project
        for channelTuner in currentlySelectedImageSerie["GlobalSettings"]["ChannelTunersArray"]:
            channelTuner.setSelectedZDepth(currentlySelectedImageSerie["GlobalSettings"]["selectedZDepth"])
            channelTuner.setSelectedZProjectMethodName(currentlySelectedImageSerie["GlobalSettings"]["selectedZProjectMethodName"])
            channelTuner.refreshShownIconImage()
        self.refreshShownIconImage()
        resultTuner = currentlySelectedImageSerie["ResultTuner"]
        resultTuner.refreshShownIconImage()

    def makeImageFileDropdownList(self):
        choixImage = self.listOfDirectoryImageFiles
        return JComboBox(choixImage)

    def getSelectedOperation(self):
        return self.selectedOperation

    def getImageDictionary(self):
        return self.imageDictionary

    def getSelectedFile(self):
        return self.selectedImageFileName

    def getSelectedSerie(self):
        return self.selectedSerie

    def getCurrentlySelectedImageSerie(self):
        return self.selectedImageSerie

    def getResultTuner(self):
        return self.currentResultDictionary

    def setResultTuner(self, newDictionary):
        self.currentResultDictionary = newDictionary

    def setCurrentlySelectedSerieOfFile(self, newFileName, newSerie):
        self.selectedImageFileName = newFileName
        self.selectedSerie = newSerie
        if str(self.selectedImageFileName) not in self.imageDictionary.keys():
            self.imageDictionary[str(self.selectedImageFileName)] = self.openImageFile(self.selectedImageFileName)
        self.selectedImageSerie = self.imageDictionary[str(self.selectedImageFileName)]["Serie "+str(self.selectedSerie)]

    def getShownIconTextDescription(self):
        return self.shownIconResultTextDescription

    def getSelectedPath(self):
        return self.selectedPath

    def getSelectedSavePath(self):
        return self.selectedSavePath

    def setSelectedSavePath(self, newPath):
        self.selectedSavePath = newPath

    def getCLIJboolean(self):
        return self.valeurSelectionBooleanCLIJ

    def getCLIJinstance(self):
        return self.clij2_instance

    def openImageFileSelector(self, event):
        imageFileSelectorDialogBox = GenericDialogPlus("Choix fichier image")
        imageFilesDropDownList = self.makeImageFileDropdownList()
        imageFilesDropDownList.setSelectedItem(self.getSelectedFile())
        channelImageFileSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        imageFileSelectorDialogBox.add(imageFilesDropDownList, channelImageFileSelectorConstraints)
        imageFileSelectorDialogBox.showDialog();
        if imageFileSelectorDialogBox.wasOKed():
            currentSelectedSerie = self.getSelectedSerie()
            newSelectedImageFile = imageFilesDropDownList.getSelectedItem()
            self.setCurrentlySelectedSerieOfFile(newSelectedImageFile, currentSelectedSerie)
            self.refreshAllCurrentShownImages() #important pour changer l'icône de l'onglet principal
        if imageFileSelectorDialogBox.wasCanceled():
            pass

    def openImageFileSerieSelector(self, event):
        imageFileSerieSelectorDialogBox = GenericDialogPlus("Choisir serie")
        def getValuesFromSerieSliders():
            vecteurSliders = imageFileSerieSelectorDialogBox.getSliders()
            serieValues = []
            for valueNumber in range(0,len(vecteurSliders)):
                serieValue = vecteurSliders[valueNumber].getValue()
                serieValues.append(serieValue)
            return serieValues
        imageDictionary = self.getImageDictionary()
        selectedImageFileName = self.getSelectedFile()
        selectedSerie = self.getSelectedSerie()
        minNbSeries = 1
        maxNbSeries = len(imageDictionary[selectedImageFileName])
        imageFileSerieSelectorDialogBox.addSlider("Serie", minNbSeries, maxNbSeries, selectedSerie)
        imageFileSerieSelectorDialogBox.showDialog();
        if imageFileSerieSelectorDialogBox.wasOKed():
            serieValues = getValuesFromSerieSliders()
            currentSelectedImageFileName = self.getSelectedFile()
            newSerieNumber = serieValues[0]
            self.setCurrentlySelectedSerieOfFile(currentSelectedImageFileName, newSerieNumber)
            self.refreshAllCurrentShownImages() #important pour changer l'icône de l'onglet principal
        if imageFileSerieSelectorDialogBox.wasCanceled():
            pass

    def openZDepthSelector(self, event):
        zDepthTunerDialogBox = GenericDialogPlus("Profondeur Z")
        def getValuesFromZDepthSliders():
            vecteurSliders = zDepthTunerDialogBox.getSliders()
            zDepthValues = []
            for valueNumber in range(0,len(vecteurSliders)):
                zDepthValue = vecteurSliders[valueNumber].getValue()
                zDepthValues.append(zDepthValue)
            return zDepthValues
        imageDictionary = self.getImageDictionary()
        selectedImageFileName = self.getSelectedFile()
        selectedSerie = self.getSelectedSerie()
        minZDepth = 1
        maxZDepth = imageDictionary[str(selectedImageFileName)]["Serie "+str(selectedSerie)]["ImagePlus"].getNSlices()
        zDepthTunerDialogBox.addSlider("Profondeur Z", minZDepth, maxZDepth, imageDictionary[str(selectedImageFileName)]["Serie "+str(selectedSerie)]["GlobalSettings"]["selectedZDepth"])#self.selectedZDepth
        zDepthTunerDialogBox.showDialog();
        if zDepthTunerDialogBox.wasOKed():
            zDepthValues = getValuesFromZDepthSliders()
            newZDepth = zDepthValues[0]
            imageDictionary[str(selectedImageFileName)]["Serie "+str(selectedSerie)]["GlobalSettings"]["selectedZDepth"] = newZDepth
            self.refreshAllCurrentShownImages()
        if zDepthTunerDialogBox.wasCanceled():
            pass

    def openZProjectMethodSelector(self, event):
        zProjectMethodSelectorDialogBox = GenericDialogPlus("Z-Project")
        imageDictionary = self.getImageDictionary()
        selectedImageFileName = self.getSelectedFile()
        selectedSerie = self.getSelectedSerie()
        zProjectDropdownList = self.makeZProjectDropdownList()
        zProjectDropdownList.setSelectedItem(imageDictionary[str(selectedImageFileName)]["Serie "+str(selectedSerie)]["GlobalSettings"]["selectedZProjectMethodName"])
        zProjectMethodSelectorDialogBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        zProjectMethodSelectorDialogBox.add(zProjectDropdownList, zProjectMethodSelectorDialogBoxConstraints)
        zProjectMethodSelectorDialogBox.showDialog();
        if zProjectMethodSelectorDialogBox.wasOKed():
            newZProjectMethodName = zProjectDropdownList.getSelectedItem()
            imageDictionary[str(selectedImageFileName)]["Serie "+str(selectedSerie)]["GlobalSettings"]["selectedZProjectMethodName"] = newZProjectMethodName
            self.refreshAllCurrentShownImages()
        if zProjectMethodSelectorDialogBox.wasCanceled():
            pass

class ChannelTuner: #Gère les réglages de chaque canal.
    """
    Rassemble les paramètres pour le réglage d'un canal. Instancié lors du lancement d'un ViewedImageSelector.
    """
    channel_tuner_number_count = 0
    def __init__(self, channelImagePlus, channelNumber, selectedZDepth, selectedZProjectMethodName, selectedOperation, valeurSelectionBooleanCLIJ, clij2_instance):
        self.channel_tuner_number = ChannelTuner.channel_tuner_number_count
        self.originalImagePlus = channelImagePlus
        self.channelNumber = channelNumber
        self.selectedZDepth = selectedZDepth
        self.selectedZProjectMethodName = selectedZProjectMethodName
        self.selectedOperation = selectedOperation
        self.valeurSelectionBooleanCLIJ = valeurSelectionBooleanCLIJ
        self.clij2_instance = clij2_instance
        self.tuningModificationFlag = False
        self.channelLutColorSelector = self.instanciateColorChooser() #JColorChooser()
        self.lutDropdownList = self.makeLutList()
        self.selectedPseudoColor = self.channelLutColorSelector.getColor() #Couleur par défaut: Color(255, 255, 255) - Blanc
        self.selectedCustomLUT = self.lutDropdownList.getItemAt(0)
        self.selectedMinPixelValue = int(0) #self.originalImagePlus.getProcessor().getMin()
        self.selectedMaxPixelValue = int(2**self.originalImagePlus.getBitDepth())-1 #self.originalImagePlus.getProcessor().getMax()
        self.gammaCorrection_A_linear_factor = 1
        self.gammaCorrection_gamma_power_factor = 1
        self.channelImagePlus = self.makeImagePlus(self.originalImagePlus)
        self.shownIconChannelTextDescription = "Preview, Channel "+str(self.channelNumber)
        self.shownIconImage = self.extractShownIconImage()

        ChannelTuner.channel_tuner_number_count+=1

    def makeLutList(self):
        lutFilesList = ["---No_custom_LUT---"]

        imageJlutPath = IJ.getDirectory("luts") #https://www.codota.com/code/java/methods/ij.IJ/getDirectory
        #print("imageJlutPath: "+str(imageJlutPath))
        imageJlutEntries = os.listdir(imageJlutPath)
        for entry in imageJlutEntries:
            lutFilesList.append(entry)
        return JComboBox(lutFilesList)

    def instanciateColorChooser(self):
        channelColorChooser = JColorChooser()
        """
        selectedSimpleColor = "White"
        def createSimplifiedColorsThumbnail():
            simplifiedColorsThumbnailItem = AbstractColorChooserPanel()
            simplifiedColorsJComboList = JComboBox(["Red", "Green", "Blue", "Cyan", "Yellow", "Magenta", "White", "Black"])
            simplifiedColorsJComboList.setSelectedItem(selectedSimpleColor)
            simplifiedColorsDictionary = {
                "Red": Color(255, 0, 0),
                "Green": Color(0, 255, 0),
                "Blue": Color(0, 0, 255),
                "Cyan": Color(0, 255, 255),
                "Yellow": Color(255, 255, 0),
                "Magenta": Color(255, 0, 255),
                "White": Color(255, 255, 255),
                "Black": Color(0, 0, 0)
            }
            simplifiedColorsThumbnailConstraints = GridBagConstraints(gridx = 1, gridy = 1)
            simplifiedColorsThumbnailItem.add(simplifiedColorsJComboList, simplifiedColorsThumbnailConstraints)
            return simplifiedColorsThumbnailItem
        simplifiedColorsThumbail = createSimplifiedColorsThumbnail()
        channelColorChooser.addChooserPanel(simplifiedColorsThumbail)
        """
        return channelColorChooser

    def makeImagePlus(self, originalImagePlus):
        channelImageWidth = originalImagePlus.getWidth()
        channelImageHeight = originalImagePlus.getHeight()
        if self.selectedZProjectMethodName == "---No_Z-Project---":
            zProjectImage = originalImagePlus
        if self.selectedZProjectMethodName != "---No_Z-Project---":
            zProjectImage = makeZProjectOnSingleChannel(originalImagePlus, self.selectedZProjectMethodName, self.valeurSelectionBooleanCLIJ, self.clij2_instance)
        newPseudoColoredChannelImagePlus = makeChannelTuningPipeline(zProjectImage, self.channelNumber, self.selectedPseudoColor, self.selectedCustomLUT, self.selectedMinPixelValue, self.selectedMaxPixelValue, self.gammaCorrection_A_linear_factor, self.gammaCorrection_gamma_power_factor, self.selectedZProjectMethodName, self.selectedOperation)
        return newPseudoColoredChannelImagePlus

    def extractShownIconImage(self):
        stackedChannelImage = self.channelImagePlus.getStack()
        if self.selectedZProjectMethodName == "---No_Z-Project---":
            zNumber = self.selectedZDepth
        if self.selectedZProjectMethodName != "---No_Z-Project---":
            zNumber = 1
        shownImageProcessor = stackedChannelImage.getProcessor(zNumber)
        shownImage = IJ.createImage("Z-Project "+str(self.selectedZProjectMethodName)+"Z-Number: "+str(zNumber), "RGB Black", self.channelImagePlus.getWidth(), self.channelImagePlus.getHeight(), 1)
        shownImage.setProcessor(shownImageProcessor)
        return shownImage

    def getShownIconImage(self):
        return self.shownIconImage

    def refreshShownIconImage(self):
        #if self.tuningModificationFlag == True:
        self.refreshImagePlus()
        newShownIconImage = self.extractShownIconImage()
        self.shownIconImage = newShownIconImage

    def refreshImagePlus(self):
        #print(self.tuningModificationFlag)
        newImagePlus = self.makeImagePlus(self.originalImagePlus)
        self.channelImagePlus = newImagePlus
        self.tuningModificationFlag = False

    def getImagePlus(self):
        return self.channelImagePlus

    def getShownIconTextDescription(self):
        return self.shownIconChannelTextDescription

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
        self.tuningModificationFlag = True

    def setSelectedCustomLUT(self,newLUT):
        self.selectedCustomLUT = newLUT
        self.tuningModificationFlag = True

    def setSelectedMinPixelValue(self, newMinPixelValue):
        self.selectedMinPixelValue = newMinPixelValue
        self.tuningModificationFlag = True

    def setSelectedMaxPixelValue(self, newMaxPixelValue):
        self.selectedMaxPixelValue = newMaxPixelValue
        self.tuningModificationFlag = True

    def setSelectedZDepth(self, newZDepth):
        self.selectedZDepth = newZDepth

    def setSelectedZProjectMethodName(self, newZProjectMethodName):
        self.selectedZProjectMethodName = newZProjectMethodName
        self.tuningModificationFlag = True

    def getSelectedZDepth(self):
        return self.selectedZDepth

    def getSelectedZProjectMethodName(self):
        return self.selectedZProjectMethodName

    def getGamma_A_LinearFactor(self):
        return self.gammaCorrection_A_linear_factor

    def getGamma_gamma_PowerFactor(self):
        return self.gammaCorrection_gamma_power_factor

    def setGamma_A_LinearFactor(self, newGamma_A_value):
        self.gammaCorrection_A_linear_factor = newGamma_A_value

    def setGamma_gamma_PowerFactor(self, newGamma_gamma_value):
        self.gammaCorrection_gamma_power_factor = newGamma_gamma_value

    def getTuningStateBoolean(self):
        return self.tuningModificationFlag

    def getSelectedOperation(self):
        return self.selectedOperation

    def getCLIJboolean(self):
        return self.valeurSelectionBooleanCLIJ

    def getCLIJinstance(self):
        return self.clij2_instance

    def openPixelBoundaryValuesTuner(self, event):
        pixelBoundaryValuesTunerDialogBox = GenericDialogPlus("Min/Max pixel values")
        def getPixelValuesFromSliders():
            vecteurSliders = pixelBoundaryValuesTunerDialogBox.getSliders()
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
        #print("Layout: "+str(self.pixelBoundaryValuesTunerDialogBox.getLayout()))
        #pixelBoundaryValuesTunerDialogBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        channelImageProcessor = self.channelImagePlus.getProcessor()
        bitDepth = channelImageProcessor.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
        minPixelBound = int(0) #Ne pas confondre getHistogramMin() avec getMin() (voir doc)
        maxPixelBound = int(2**bitDepth)-1 #Ne pas confondre getHistogramMax() avec getMax() (voir doc)
        pixelBoundaryValuesTunerDialogBox.addSlider("Pixel minimum histogramme", minPixelBound, maxPixelBound, self.selectedMinPixelValue)
        #self.pixelBoundaryValuesTunerDialogBox.addToSameRow() # The next item is appended next to the last one
        pixelBoundaryValuesTunerDialogBox.addSlider("Pixel maximum histogramme", minPixelBound, maxPixelBound, self.selectedMaxPixelValue)
        pixelBoundaryValuesTunerDialogBox.showDialog();
        if pixelBoundaryValuesTunerDialogBox.wasOKed():
            minHistogramPixelValues, maxHistogramPixelValues = getPixelValuesFromSliders()
            newMinPixelValue = minHistogramPixelValues[0]
            self.setSelectedMinPixelValue(newMinPixelValue)
            newMaxPixelValue = maxHistogramPixelValues[0]
            self.setSelectedMaxPixelValue(newMaxPixelValue)
            self.refreshShownIconImage()
        if pixelBoundaryValuesTunerDialogBox.wasCanceled():
            pass

    def openColorChooser(self, event):
        #https://www.tutorialspoint.com/jython/jython_layout_management.htm
        colorChooserDialogBox = GenericDialogPlus("Channel color selector")
        #print("Layout: "+str(self.colorChooserDialogBox.getLayout()))
        channelLutColorSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        colorChooserDialogBox.add(self.channelLutColorSelector, channelLutColorSelectorConstraints)
        colorChooserDialogBox.showDialog();
        if colorChooserDialogBox.wasOKed():
            newColor = self.channelLutColorSelector.getColor()
            self.setSelectedPseudoColor(newColor)
            self.refreshShownIconImage()
        if colorChooserDialogBox.wasCanceled():
            pass

    def openLutChooser(self, event):
        lutChooserDialogBox = GenericDialogPlus("Custom LUT selector")
        #print("Layout: "+str(self.lutChooserDialogBox.getLayout()))
        channelCustomLutSelectorConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        lutChooserDialogBox.add(self.lutDropdownList, channelCustomLutSelectorConstraints)
        lutChooserDialogBox.showDialog();
        if lutChooserDialogBox.wasOKed():
            newLUT = self.lutDropdownList.getSelectedItem()
            self.setSelectedCustomLUT(newLUT)
            self.refreshShownIconImage()
        if lutChooserDialogBox.wasCanceled():
            pass

    def openGammaCorrectionTuner(self, event):
        gammaCorrectionDialogBox = GenericDialogPlus("Set Gamma correction parameters")
        digitsNumber = 2
        gammaCorrectionDialogBox.addNumericField("Coefficient lineaire A", self.getGamma_A_LinearFactor(), digitsNumber)
        gammaCorrectionDialogBox.addNumericField("Cefficient de puissance Gamma", self.getGamma_gamma_PowerFactor(), digitsNumber)
        gammaCorrectionDialogBox.showDialog()
        if gammaCorrectionDialogBox.wasOKed():
            vecteurNumericFields = gammaCorrectionDialogBox.getNumericFields()
            inputGamma_A_LinearFactor = vecteurNumericFields[0]
            newGamma_A_LinearFactor = Float.parseFloat(inputGamma_A_LinearFactor.getText())
            self.setGamma_A_LinearFactor(newGamma_A_LinearFactor)
            inputGamma_gamma_PowerFactor = vecteurNumericFields[1]
            newGamma_gamma_PowerFactor = Float.parseFloat(inputGamma_gamma_PowerFactor.getText())
            self.setGamma_gamma_PowerFactor(newGamma_gamma_PowerFactor)
            self.refreshShownIconImage()
        if gammaCorrectionDialogBox.wasCanceled():
            pass

class ResultTuner: #Classe mère des ResultTuners ci-dessous
    """
    Classe mère des ResultTuners (MontageTuner et CompositeTuner) décrites plus bas.
    Gère les paramètres communs à toutes les images d'output (calibration et redimensionnement)
    """
    def __init__(self, selectedImageSerie, valeurSelectionBooleanCLIJ, clij2_instance):
        self.selectedImage = selectedImageSerie
        self.valeurSelectionBooleanCLIJ = valeurSelectionBooleanCLIJ
        self.clij2_instance = clij2_instance
        self.resizeFactor = 1
        self.xUnit = self.selectedImage["ImagePlus"].getCalibration().getXUnit()
        self.yUnit = self.selectedImage["ImagePlus"].getCalibration().getYUnit()
        self.xPixelSize = self.selectedImage["ImagePlus"].getCalibration().pixelWidth
        self.yPixelSize = self.selectedImage["ImagePlus"].getCalibration().pixelHeight

    def get_X_unit(self):
        return self.xUnit

    def set_X_unit(self, newText):
        self.xUnit = newText

    def get_Y_unit(self):
        return self.yUnit

    def set_Y_unit(self, newText):
        self.yUnit = newText

    def getXPixelSize(self):
        return self.xPixelSize

    def setXPixelSize(self, newValue):
        self.xPixelSize = newValue

    def getYPixelSize(self):
        return self.yPixelSize

    def setYPixelSize(self, newValue):
        self.yPixelSize = newValue

    def getResizeFactor(self):
        return self.resizeFactor

    def setResizeFactor(self, newValue):
        self.resizeFactor = newValue

    def getCLIJboolean(self):
        return self.valeurSelectionBooleanCLIJ

    def getCLIJinstance(self):
        return self.clij2_instance

    def openPixelSizeChangerWindow(self, event):
        pixelSizeChangerBox = GenericDialogPlus("Entrer le coefficient de redimensionnement")
        digitsNumber = 2
        charNumber = 50
        pixelSizeChangerBox.addNumericField("Taille pixel en X", self.getXPixelSize(), digitsNumber)
        pixelSizeChangerBox.addStringField("Unite mesure pour X", self.get_X_unit(), charNumber)
        pixelSizeChangerBox.addNumericField("Taille pixel en Y", self.getYPixelSize(), digitsNumber)
        pixelSizeChangerBox.addStringField("Unite mesure pour Y", self.get_Y_unit(), charNumber)
        pixelSizeChangerBox.showDialog()
        if pixelSizeChangerBox.wasOKed():
            vecteurNumericFields = pixelSizeChangerBox.getNumericFields()
            vecteurStringFields = pixelSizeChangerBox.getStringFields()
            inputXPixelSize = vecteurNumericFields[0]
            newXPixelSize = Float.parseFloat(inputXPixelSize.getText())
            self.setXPixelSize(newXPixelSize)
            inputXUnitSize = vecteurStringFields[0]
            self.set_X_unit(inputXUnitSize)
            inputYPixelSize = vecteurNumericFields[1]
            newYPixelSize = Float.parseFloat(inputYPixelSize.getText())
            self.setYPixelSize(newYPixelSize)
            inputYUnitSize = vecteurStringFields[1]
            self.set_Y_unit(inputYUnitSize)
        if pixelSizeChangerBox.wasCanceled():
            pass

    def openResizeFactorEntryWindow(self, event):
        resizeFactorEntryBox = GenericDialogPlus("Entrer le coefficient de redimensionnement")
        digitsNumber = 2
        resizeFactorEntryBox.addNumericField("Coefficient", self.getResizeFactor(), digitsNumber)
        resizeFactorEntryBox.showDialog()
        if resizeFactorEntryBox.wasOKed():
            vecteurNumericFields = resizeFactorEntryBox.getNumericFields()
            inputResizeFactor = vecteurNumericFields[0]
            newResizeFactor = Float.parseFloat(inputResizeFactor.getText())
            self.setResizeFactor(newResizeFactor)
        if resizeFactorEntryBox.wasCanceled():
            pass

class MontageTuner(ResultTuner): #Gère les paramètres spécifiques pour les montages (nombre de lignes et de colonnes, images sélectionnées)
    """
    Gère les paramètres spécifiques pour les montages (nombre de lignes et de colonnes, images sélectionnées) et affiche l'icône.

    Voir aussi:
    #https://www.geeksforgeeks.org/reorder-a-array-according-to-given-indexes/
    #https://imagej.nih.gov/ij/developer/api/ij/plugin/MontageMaker.html
    """
    def __init__(self, selectedImageSerie, valeurSelectionBooleanCLIJ, clij2_instance):
        ResultTuner.__init__(self, selectedImageSerie, valeurSelectionBooleanCLIJ, clij2_instance)
        self.numberOfColumns = 1
        self.numberOfRows = 1
        #self.numberOfColumns, self.numberOfRows = self.autoAdjustMontageSize()
        self.listOfAssignedImages = self.makeEmptyListOfSelectedImages()
        self.listOfJComboBoxes = self.makeListOfJComboBoxes()
        self.montageCurrentImagePlus = self.makeMontageImagePlus()
        self.shownIconChannelTextDescription = "Montage, Z-Depth "+str(self.selectedImage["GlobalSettings"]["selectedZDepth"])+" Z-Project "+str(self.selectedImage["GlobalSettings"]["selectedZProjectMethodName"])
        self.shownIconImage = self.extractShownIconImage()

    def makeChoiceListOfImages(self):
        dictionaryOfPreMontageImages = self.selectedImage["ResultImagesDictionary"]
        dictKeys = dictionaryOfPreMontageImages.keys()
        return dictKeys

    def makeListOfJComboBoxes(self):
        JComboBoxList = []
        listChoiceOfImages = self.makeChoiceListOfImages()
        for imageNumber in range(0, len(self.listOfAssignedImages)):
            cellJComboBox = JComboBox(listChoiceOfImages)
            cellJComboBox.setSelectedItem(self.listOfAssignedImages[imageNumber])
            JComboBoxList.append(cellJComboBox)
        return JComboBoxList

    def resetJComboBoxes(self):
        self.listOfJComboBoxes = self.makeListOfJComboBoxes()

    def refreshJComboBoxes(self):
        listNumber = 0
        for jComboBox in self.listOfJComboBoxes:
            jComboBox.setSelectedItem(self.listOfAssignedImages[listNumber])
            listNumber+=1

    def getListOfJComboBoxes(self):
        return self.listOfJComboBoxes

    def makeMontageImagePlus(self):
        zDepthPreMontageImagesArray = makeArrayOfPreMontageImages(self.listOfAssignedImages, self.selectedImage["ResultImagesDictionary"])
        montageImp = stackMontages(zDepthPreMontageImagesArray, self.numberOfColumns, self.numberOfRows, False, self.clij2_instance) #self.valeurSelectionBooleanCLIJ
        return montageImp

    def getMontageImagePlus(self):
        return self.montageCurrentImagePlus

    def extractShownIconImage(self):
        selectedZDepth = self.selectedImage["GlobalSettings"]["selectedZDepth"]
        selectedZProjectMethodName = self.selectedImage["GlobalSettings"]["selectedZProjectMethodName"]
        montageImagePlusStack = self.montageCurrentImagePlus.getStack()
        if selectedZProjectMethodName == "---No_Z-Project---":
            zNumber = selectedZDepth
        if selectedZProjectMethodName != "---No_Z-Project---":
            zNumber = 1
        shownImageProcessor = montageImagePlusStack.getProcessor(zNumber)
        shownImage = IJ.createImage("Montage, Z-Project "+str(selectedZProjectMethodName)+"Z-Number: "+str(zNumber), "RGB Black", self.montageCurrentImagePlus.getWidth(), self.montageCurrentImagePlus.getHeight(), 1)
        shownImage.setProcessor(shownImageProcessor)
        return shownImage

    def refreshShownIconImage(self):
        self.montageCurrentImagePlus = self.makeMontageImagePlus()
        newShownIconImage = self.extractShownIconImage()
        self.shownIconImage = newShownIconImage

    def getShownIconImage(self):
        return self.shownIconImage

    def getShownIconTextDescription(self):
        return self.shownIconChannelTextDescription

    def makeEmptyListOfSelectedImages(self):
        arrayOfSelections = []
        for number in range(0, self.numberOfColumns*self.numberOfRows):
            arrayOfSelections.append("---Empty---")
        return arrayOfSelections

    def getListOfAssignableImages(self):
        return self.selectedImage["ResultImagesDictionary"]

    def getListOfAssignedImages(self):
        return self.listOfAssignedImages

    def setListOfAssignedImages(self, newList):
        self.listOfAssignedImages = newList
        self.arrayOfPreMontageImages = makeArrayOfPreMontageImages(self.listOfAssignedImages, self.selectedImage["ResultImagesDictionary"])

    def autoAdjustMontageSize(self): #Pas au point - Désactivé
        numberOfSlices = len(self.selectedImage["ResultImagesDictionary"])-1
        numberOfColumns = int(math.floor(math.sqrt(numberOfSlices)))
        if (numberOfColumns*numberOfColumns < numberOfSlices):
            numberOfColumns += 1
        numberOfRows = numberOfColumns
        if (numberOfSlices <= numberOfColumns*(numberOfRows-1)):
            numberOfRows += 1

        return numberOfColumns, numberOfRows

    def getNumberOfRows(self):
        return self.numberOfRows

    def setNumberOfRows(self, newValue):
        self.numberOfRows = newValue

    def getNumberOfColumns(self):
        return self.numberOfColumns

    def setNumberOfColumns(self, newValue):
        self.numberOfColumns = newValue

    def openNumberRowColumnsWindow(self, event):
        montageLinesColumnsBox = GenericDialogPlus("Entrer les valeurs")
        digitsNumber = 0
        montageLinesColumnsBox.addNumericField("Nombre de lignes du montage", self.getNumberOfRows(), digitsNumber)
        montageLinesColumnsBox.addNumericField("Nombre de colonnes du montage", self.getNumberOfColumns(), digitsNumber)
        montageLinesColumnsBox.showDialog()
        if montageLinesColumnsBox.wasOKed():
            vecteurNumericFields = montageLinesColumnsBox.getNumericFields()
            inputNumberOfRows = vecteurNumericFields[0]
            newNumberOfRows = Integer.parseInt(inputNumberOfRows.getText())
            self.setNumberOfRows(newNumberOfRows)
            inputNumberOfColumns = vecteurNumericFields[1]
            newNumberOfColumns = Integer.parseInt(inputNumberOfColumns.getText())
            self.setNumberOfColumns(newNumberOfColumns)
            arrayOfImages = self.makeEmptyListOfSelectedImages()
            self.setListOfAssignedImages(arrayOfImages)
            self.resetJComboBoxes()
            self.refreshShownIconImage()

    def openImageAssignatorWindow(self, event):
        imageAssignatorBox = GenericDialogPlus("Assigner les images")
        listOfCellAssignators = self.getListOfJComboBoxes()
        listOfCurrentlyAssignedImages = self.getListOfAssignedImages()
        imageAssignatorBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        position = 1
        cellAssignatorNumber = 0
        for cellAssignator in listOfCellAssignators:
            cellAssignator.setSelectedItem(listOfCurrentlyAssignedImages[cellAssignatorNumber])
            imageAssignatorItemConstraints = imageAssignatorBoxConstraints
            imageAssignatorItemConstraints.gridy = position
            imageAssignatorBox.add(cellAssignator, imageAssignatorItemConstraints)
            position += 2
            cellAssignatorNumber += 1
        imageAssignatorBox.showDialog()
        if imageAssignatorBox.wasOKed():
            arrayOfImages = []
            for cellAssignator in listOfCellAssignators:
                selectedImage = cellAssignator.getSelectedItem()
                arrayOfImages.append(selectedImage)
            print(arrayOfImages)
            self.setListOfAssignedImages(arrayOfImages)
            self.refreshJComboBoxes()
            self.refreshShownIconImage()

class CompositeTuner(ResultTuner): #Gère les paramètres spécifiques des images composites (type d'image)
    """
    Gère les paramètres spécifiques des images composites (type d'image)
    """
    def __init__(self, selectedImageSerie, valeurSelectionBooleanCLIJ, clij2_instance):
        ResultTuner.__init__(self, selectedImageSerie, valeurSelectionBooleanCLIJ, clij2_instance)
        self.displayModeValue = "Color"

        self.previewRedimensionCoef = 0.125
        self.compositeCurrentImagePlus = self.makeCompositeImagePlus()
        self.shownIconChannelTextDescription = "Composite, Z-Depth "+str(self.selectedImage["GlobalSettings"]["selectedZDepth"])+" Z-Project "+str(self.selectedImage["GlobalSettings"]["selectedZProjectMethodName"])
        self.shownIconImage = self.extractShownIconImage()

    def makeImageTypeList(self):
        choixTypeImage = ["Color", "Composite", "Grayscale"]
        return JComboBox(choixTypeImage)

    def setImageType(self, newType):
        self.displayModeValue = newType

    def getImageType(self):
        return self.displayModeValue

    def makeCompositeImagePlus(self):
        #zDepthPreMontageImagesArray = makeArrayOfPreMontageImages(self.listOfAssignedImages, self.selectedImage["ResultImagesDictionary"])
        #montageImp = stackMontages(zDepthPreMontageImagesArray, self.numberOfColumns, self.numberOfRows)

        if self.displayModeValue == "Color":
            typeValue = 2
        if self.displayModeValue == "Composite":
            typeValue = 1
        if self.displayModeValue == "Grayscale":
            typeValue = 3
        """
        originalImagePlusComposite = CompositeImage(self.selectedImage["ImagePlus"], typeValue)
        redimensionCoef = self.previewRedimensionCoef
        imagePlusComposite = originalImagePlusComposite.resize(int(redimensionCoef*originalImagePlusComposite.getWidth()), int(redimensionCoef*originalImagePlusComposite.getHeight()), "bilinear") # "bilinear" or "none"

        channelNumber = 0
        for channelTuner in self.selectedImage["GlobalSettings"]["ChannelTunersArray"]:
            channelNumber+=1
            minHistogramPixelValue = channelTuner.getSelectedMinPixelValue()
            maxHistogramPixelValue = channelTuner.getSelectedMaxPixelValue()
            selectedLUT = channelTuner.getSelectedCustomLUT()
            channelPseudoColor = channelTuner.getSelectedPseudoColor()
            channelImageProcessor = imagePlusComposite.getProcessor() #Ne pas mettre l'indice -> les canaux seront parcourus séquentiellement
            correctedMinPixelValue, correctedMaxPixelValue = calculateCorrectedMinMaxPixelValues(channelImageProcessor, minHistogramPixelValue, maxHistogramPixelValue)
            channelImageProcessor.setMinAndMax(correctedMinPixelValue, correctedMaxPixelValue) #Ne pas confondre setHistogramRange() avec setMinAndMax() (voir doc)
            #print("channelImageProcessor: ", channelImageProcessor)
            if selectedLUT != "---No_custom_LUT---":
                lutPath = IJ.getDirectory("luts")
                customLUT = LutLoader.openLut(lutPath+selectedLUT)
                imagePlusComposite.setChannelLut(customLUT, channelNumber)
            if selectedLUT == "---No_custom_LUT---":
                singleColorLUT = imagePlusComposite.createLutFromColor(channelPseudoColor)
                imagePlusComposite.setChannelLut(singleColorLUT, channelNumber)
        """
        redimensionCoef = self.previewRedimensionCoef
        resizedImagePlus = self.selectedImage["ImagePlus"].resize(int(redimensionCoef*self.selectedImage["ImagePlus"].getWidth()), int(redimensionCoef*self.selectedImage["ImagePlus"].getHeight()), "bilinear") # "bilinear" or "none"

        zProjectedTunedImages = makeTunedChannelImages(resizedImagePlus, self.selectedImage["GlobalSettings"]["ChannelTunersArray"])
        compositeFusedChannelsImage = makeFusedChannelsCompositeImage(zProjectedTunedImages)
        imagePlusComposite = CompositeImage(compositeFusedChannelsImage, typeValue)

        return imagePlusComposite

    def getCompositeImagePlus(self):
        return self.compositeCurrentImagePlus

    def extractShownIconImage(self):
        selectedZDepth = self.selectedImage["GlobalSettings"]["selectedZDepth"]
        selectedZProjectMethodName = self.selectedImage["GlobalSettings"]["selectedZProjectMethodName"]
        compositeImagePlusStack = self.compositeCurrentImagePlus.getStack()
        if selectedZProjectMethodName == "---No_Z-Project---":
            zNumber = selectedZDepth
        if selectedZProjectMethodName != "---No_Z-Project---":
            zNumber = 1
        shownImageProcessor = compositeImagePlusStack.getProcessor(zNumber)
        shownImage = IJ.createImage("Composite, Z-Project "+str(selectedZProjectMethodName)+"Z-Number: "+str(zNumber), "composite-mode", self.compositeCurrentImagePlus.getWidth(), self.compositeCurrentImagePlus.getHeight(), 1)
        shownImage.setProcessor(shownImageProcessor)
        return shownImage

    def refreshShownIconImage(self):
        self.compositeCurrentImagePlus = self.makeCompositeImagePlus()
        newShownIconImage = self.extractShownIconImage()
        self.shownIconImage = newShownIconImage

    def getShownIconImage(self):
        return self.shownIconImage

    def getShownIconTextDescription(self):
        return self.shownIconChannelTextDescription

    def openImageTypeWindow(self, event):
        imageTypeWindowBox = GenericDialogPlus("Selectionner reglage")
        imageTypeDropdownList = self.makeImageTypeList()
        imageTypeDropdownList.setSelectedItem(self.displayModeValue)
        imageTypeWindowBoxConstraints = GridBagConstraints(gridx = 1, gridy = 1)
        imageTypeWindowBox.add(imageTypeDropdownList, imageTypeWindowBoxConstraints)
        imageTypeWindowBox.showDialog();
        if imageTypeWindowBox.wasOKed():
            newImageType = imageTypeDropdownList.getSelectedItem()
            self.setImageType(newImageType)
            self.refreshShownIconImage()
        if imageTypeWindowBox.wasCanceled():
            pass

class InterfaceInstance: #Gère le système d'interface graphique.
    """
    Gère le système d'interface graphique multionglet. Associe chaque tuner à son propre onglet.
    Lors d'un changement d'image, efface les onglets (ChannelTuners et ResultTuner) associés à cette image de l'interface et place les nouveaux.
    Les états des onglets sont conservés dans un dictionnaire: créés si l'image n'a encore jamais été visualisée,
    et récupérés depuis le dictionnaire si sélection d'une image déjà visualisée antérieurement.
    Permet aussi de mettre à jour les icônes d'images de résultat (image fusionnée, montage...) lors des changements opérés sur les canaux.
    Permet aussi de mettre à jour toutes les icônes en cas de changement de profondeur Z ou de Z-projection.
    """
    def __init__(self, imageSelector, imageTuningDialogBox):
        self.imageSelector = imageSelector
        self.imageTuningDialogBox = imageTuningDialogBox
        self.selectedChannelTuner = self.imageSelector.getCurrentlySelectedImageSerie()["GlobalSettings"]["ChannelTunersArray"][0]
        self.mainThumbnail = self.createMainThumbnail()
        self.dictionaryOfThumbnails = self.instanciateDictionaryOfThumbnails()
        self.currentActiveThumbnails = self.dictionaryOfThumbnails[str(self.imageSelector.getCurrentlySelectedImageSerie()["ImagePlus"].getTitle())]
        self.currentMultiTab = self.instanciateMultiTab()

    def setNewImageSelector(self, newImageSelector): #normally not needed
        self.imageSelector = newImageSelector

    def setNewChannelTuner(self, newChannelTuner): #needed to change channelTuner associated to thumbnail
        self.selectedChannelTuner = newChannelTuner

    def getSelectedChannelTuner(self):
        return self.selectedChannelTuner

    def getDictionaryOfThumbnails(self):
        return self.dictionaryOfThumbnails

    def setSelectedThumbnails(self):
        currentlySelectedImageSerie = self.imageSelector.getCurrentlySelectedImageSerie()
        imageTitle = currentlySelectedImageSerie["ImagePlus"].getTitle()
        if str(imageTitle) in self.dictionaryOfThumbnails.keys():
            self.currentActiveThumbnails = self.dictionaryOfThumbnails[str(imageTitle)]
        if str(imageTitle) not in self.dictionaryOfThumbnails.keys():
            self.dictionaryOfThumbnails[str(imageTitle)] = {}
            self.dictionaryOfThumbnails[str(imageTitle)]["ChannelThumbnails"] = self.createChannelTunersThumbnailsList()
            self.dictionaryOfThumbnails[str(imageTitle)]["ResultThumbnail"] = self.createResultThumbnail()
            self.currentActiveThumbnails = self.dictionaryOfThumbnails[str(imageTitle)]

    def getCurrentThumbnails(self):
        return self.currentActiveThumbnails

    def instanciateDictionaryOfThumbnails(self):
        dictionaryOfThumbnails = {}
        currentlySelectedImageSerie = self.imageSelector.getCurrentlySelectedImageSerie()
        imageTitle = currentlySelectedImageSerie["ImagePlus"].getTitle()
        dictionaryOfThumbnails[str(imageTitle)] = {}
        dictionaryOfThumbnails[str(imageTitle)]["ChannelThumbnails"] = self.createChannelTunersThumbnailsList()
        dictionaryOfThumbnails[str(imageTitle)]["ResultThumbnail"] = self.createResultThumbnail()

        return dictionaryOfThumbnails

    def instanciateMultiTab(self):
        currentlySelectedImageSerie = self.imageSelector.getCurrentlySelectedImageSerie()
        imageTitle = currentlySelectedImageSerie["ImagePlus"].getTitle()
        currentlySelectedThumbnails = self.dictionaryOfThumbnails[str(imageTitle)]
        channelThumbnails = currentlySelectedThumbnails["ChannelThumbnails"]
        resultThumbnail = currentlySelectedThumbnails["ResultThumbnail"]

        #Instancier multi-onglets
        imageTuningDialogBoxTabs = JTabbedPane()

        masterThumbail = self.mainThumbnail
        imageTuningDialogBoxTabs.addTab("Image Selector", masterThumbail)

        channelNumber = 1
        for channelThumbnail in channelThumbnails:
            channelTitle = str(imageTitle)+", Canal "+str(channelNumber)
            imageTuningDialogBoxTabs.addTab(channelTitle, channelThumbnail)
            channelNumber+=1

        if self.imageSelector.selectedOperation == "Make Montage":
            imageTuningDialogBoxTabs.addTab(str(imageTitle)+", Montage tuning", resultThumbnail)
        if self.imageSelector.selectedOperation == "Make Composite":
            imageTuningDialogBoxTabs.addTab(str(imageTitle)+", Composite tuning", resultThumbnail)
        #imageTuningDialogBoxTabs.addTab("Global", launchingThumbnail)

        return imageTuningDialogBoxTabs

    def getCurrentMultiTab(self):
        return self.currentMultiTab

    def refreshMultiTab(self):
        currentlySelectedImageSerie = self.imageSelector.getCurrentlySelectedImageSerie()
        self.setSelectedThumbnails()
        imageTitle = currentlySelectedImageSerie["ImagePlus"].getTitle()
        currentlySelectedThumbnails = self.dictionaryOfThumbnails[str(imageTitle)]
        channelThumbnails = currentlySelectedThumbnails["ChannelThumbnails"]
        resultThumbnail = currentlySelectedThumbnails["ResultThumbnail"]

        #Effacer les tabs précédents
        numberOfTabs = self.currentMultiTab.getTabCount()
        for index in range(numberOfTabs-1, 0, -1):
            self.currentMultiTab.removeTabAt(index)

        #Ajouter les nouveaux tabs
        channelNumber = 1
        for channelThumbnail in channelThumbnails:
            channelTitle = str(imageTitle)+", Canal "+str(channelNumber)
            self.currentMultiTab.addTab(channelTitle, channelThumbnail)
            channelNumber+=1

        if self.imageSelector.selectedOperation == "Make Montage":
            self.currentMultiTab.addTab(str(imageTitle)+", Montage tuning", resultThumbnail)
        if self.imageSelector.selectedOperation == "Make Composite":
            self.currentMultiTab.addTab(str(imageTitle)+", Composite tuning", resultThumbnail)

    def initializeBoxMultiTabContent(self):
        self.imageTuningDialogBox.setContentPane(self.getCurrentMultiTab())

    def setShownIcon(self, tuner, iconJLabel):
        newShownIcon = self.generateIcon(tuner)
        iconJLabel.setIcon(newShownIcon)

    def instanciateShownIcon(self, tuner):
        shownIconJLabel = JLabel()
        self.setShownIcon(tuner, shownIconJLabel)
        return shownIconJLabel

    def generateIcon(self, tuner):
        shownImagePlus = tuner.getShownIconImage()
        #shownImagePlus.show()
        shownTextDescription = tuner.getShownIconTextDescription()
        previewAWTimage = shownImagePlus.getImage()
        shownIconWidth = int(shownImagePlus.getWidth())
        if shownIconWidth == 0:
            shownIconWidth = 1
        shownIconHeight = int(shownImagePlus.getHeight())
        if shownIconHeight == 0:
            shownIconHeight = 1
        resizedPreviewAWTimage = previewAWTimage.getScaledInstance(shownIconWidth, shownIconHeight, 0)
        newShownIcon = ImageIcon(resizedPreviewAWTimage, shownTextDescription)
        return newShownIcon

    def refreshAllIcons(self):
        currentlySelectedImageSerie = self.imageSelector.getCurrentlySelectedImageSerie()
        channelTuners = currentlySelectedImageSerie["GlobalSettings"]["ChannelTunersArray"]
        resultTuner = currentlySelectedImageSerie["ResultTuner"]
        currentThumbnails = self.getCurrentMultiTab()
        currentThumbnailsComponents = currentThumbnails.getComponents()
        mainThumbnailComponents = currentThumbnailsComponents[0].getComponents()
        mainThumbnailIcon = mainThumbnailComponents[0]
        self.setShownIcon(self.imageSelector, currentThumbnails.getComponents()[0].getComponents()[0]) #mainThumbnailIcon
        channelNumber = 1
        for channelTuner in channelTuners:
            channelThumbnailIcon = currentThumbnailsComponents[channelNumber].getComponents()[0]
            self.setShownIcon(channelTuner, currentThumbnails.getComponents()[channelNumber].getComponents()[0]) #channelThumbnailIcon
            channelNumber+=1
        #if self.imageSelector.selectedOperation == "Make Montage":
        resultThumbnailIcon = currentThumbnailsComponents[-1].getComponents()[0]
        self.setShownIcon(resultTuner, currentThumbnails.getComponents()[-1].getComponents()[0]) #resultThumbnailIcon

    def getLoadedImages(self):
        return self.imageSelector.getImageDictionary()

    def createChannelTunersThumbnailsList(self):
        currentStateDictionary = self.getLoadedImages()
        currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
        channelTuners = currentlySelectedImageSerie["GlobalSettings"]["ChannelTunersArray"]
        channelThumbnailsList = []
        for channelTuner in channelTuners:
            self.setNewChannelTuner(channelTuner)
            channelTunerTab = self.createChannelThumbnail(channelTuner)
            channelThumbnailsList.append(channelTunerTab)
        return channelThumbnailsList

    def createMainThumbnail(self):
        mainThumbnailItem = JPanel(False)
        buttonsGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = GridBagConstraints.REMAINDER,
            gridheight = 1,
            weightx = 0.0,
            weighty = 0.0,
        )
        #buttonsGridBagConstraints.insets.left = 5
        #buttonsGridBagConstraints.insets.right = 5
        imageIconGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = 1,
            gridheight = 2,
            weightx = 0.0,
            weighty = 1.0
        )

        shownMainIconJLabel = self.instanciateShownIcon(self.imageSelector)

        def openImageFileSelector(event):
            self.imageSelector.openImageFileSelector(event)
            self.setShownIcon(self.imageSelector, shownMainIconJLabel)
            self.refreshMultiTab()
        imageFileSelectorButton = JButton("Select image file", actionPerformed = openImageFileSelector)

        def openImageFileSerieSelector(event):
            self.imageSelector.openImageFileSerieSelector(event)
            self.setShownIcon(self.imageSelector, shownMainIconJLabel)
            self.refreshMultiTab()
        imageFileSerieSelectorButton = JButton("Select serie", actionPerformed = openImageFileSerieSelector)

        def openZDepthSelector(event):
            self.imageSelector.openZDepthSelector(event)
            self.setShownIcon(self.imageSelector, shownMainIconJLabel)
            self.refreshAllIcons()
        zDepthButton = JButton("Change Z-Depth", actionPerformed = openZDepthSelector)

        def openZProjectMethodSelector(event):
            self.imageSelector.openZProjectMethodSelector(event)
            self.setShownIcon(self.imageSelector, shownMainIconJLabel)
            self.refreshAllIcons()
        zProjectMethodButton = JButton("Select Z-Project method", actionPerformed = openZProjectMethodSelector)

        def setFileSavePath(event):
            savePathSelectorDialogBox = GenericDialogPlus("Choix repertoire de sauvegarde")
            savePathSelectorDialogBox.addDirectoryField("Choisir un repertoire pour deposer les fichiers obtenus", self.imageSelector.getSelectedSavePath())
            savePathSelectorDialogBox.showDialog();
            if savePathSelectorDialogBox.wasOKed():
                save_folder = savePathSelectorDialogBox.getNextString()
                self.imageSelector.setSelectedSavePath(save_folder)
        savePathButton = JButton("Set dump directory", actionPerformed = setFileSavePath)

        def globalPipeline(event):
            self.imageTuningDialogBox.dispose()
            impNumber = 0
            dumpSaveFilePath = self.imageSelector.getSelectedSavePath()
            separator = self.imageSelector.getSeparator()
            imageFilesList = self.imageSelector.getListOfImageFiles()
            selectedPath = self.imageSelector.getSelectedPath()
            selectedOperation = self.imageSelector.getSelectedOperation()
            selectedZProjectMethodName = self.imageSelector.getCurrentlySelectedImageSerie()["GlobalSettings"]["selectedZProjectMethodName"]
            selectedChannelTuners = self.imageSelector.getCurrentlySelectedImageSerie()["GlobalSettings"]["ChannelTunersArray"]
            selectedResultTuner = self.imageSelector.getCurrentlySelectedImageSerie()["ResultTuner"]
            valeurSelectionBooleanCLIJ = self.imageSelector.getCLIJboolean()
            clij2_instance = self.imageSelector.getCLIJinstance()

            redimensionCoef = selectedResultTuner.getResizeFactor()
            xUnit = selectedResultTuner.get_X_unit()
            xPixelSize = selectedResultTuner.getXPixelSize()
            yUnit = selectedResultTuner.get_Y_unit()
            yPixelSize = selectedResultTuner.getYPixelSize()

            dictionaryOfRealImages = {}
            for imageFile in imageFilesList:
                dictionaryOfRealImages[str(imageFile)] = self.imageSelector.openImageFile(imageFile)
                #print("FILE: "+str(imageFile))
                #imagePlusFileInfo = imageFile.getFileInfo()
                #print("File_INFO: "+str(imagePlusFileInfo))
                #imagePlusFilePath = imagePlusFileInfo.getFilePath()
                impNumber+=1
                serieNumber = 0
                for serie in dictionaryOfRealImages[str(imageFile)]:
                    #print("Serie: ", serie)
                    serieNumber+=1
                    imagePlusFilePath = str(selectedPath)+separator+str(imageFile)
                    print(imagePlusFilePath)
                    currentImagePlus = dictionaryOfRealImages[imageFile]["Serie "+str(serieNumber)]["ImagePlus"]
                    print("Processing "+currentImagePlus.getTitle())

                    imageCalibration = currentImagePlus.getCalibration()
                    resizedImagePlus = currentImagePlus.resize(int(redimensionCoef*currentImagePlus.getWidth()), int(redimensionCoef*currentImagePlus.getHeight()), "bilinear") # "bilinear" or "none"
                    resizedImageCalibration = Calibration()
                    resizedImageCalibration.setXUnit(String(xUnit))
                    resizedImageCalibration.setXUnit(String(yUnit))
                    resizedImageCalibration.pixelHeight = yPixelSize/redimensionCoef
                    resizedImageCalibration.pixelWidth = xPixelSize/redimensionCoef
                    resizedImagePlus.setCalibration(resizedImageCalibration)

                    #selectedZProjectMethodName = dictionaryOfRealImages[imageFile]["Serie "+str(serieNumber)]["GlobalSettings"]["selectedZProjectMethodName"]

                    if selectedZProjectMethodName != "---No_Z-Project---":
                        if valeurSelectionBooleanCLIJ == False:
                            zProjectedImagePlus = makeZProject(resizedImagePlus, selectedZProjectMethodName)
                            #zProjectedImagePlus = makeImageJZProject(imagePlus, selectedZProjectMethodName)
                        if valeurSelectionBooleanCLIJ == True:
                            currentImageBuffer = clij2_instance.push(resizedImagePlus)
                            zProjectedImageBuffer = makeZProject_CLIJ2(currentImageBuffer, selectedZProjectMethodName, clij2_instance)#makeZProject(currentImageBuffer, selectedZProjectMethodName)
                            zProjectedImagePlus = clij2_instance.pull(zProjectedImageBuffer)
                    if selectedZProjectMethodName == "---No_Z-Project---":
                        zProjectedImagePlus = resizedImagePlus

                    if selectedOperation == "Make Composite":
                        resultImagePlus = makeCompositePipeline(zProjectedImagePlus, selectedChannelTuners, selectedResultTuner)
                        #resultImagePlus.show()
                        fileName = (imagePlusFilePath.split(separator)[-1]).split(".")[0]
                        dumpFileName = "Composite_"+str(selectedZProjectMethodName)+"_"+str(fileName)+"_"+str(impNumber)+"_"+str(serieNumber)
                    if selectedOperation == "Make Montage":

                        resultImagePlus = makeMontagePipeline(zProjectedImagePlus, selectedChannelTuners, selectedResultTuner)
                        #resultImagePlus.show()
                        fileName = (imagePlusFilePath.split(separator)[-1]).split(".")[0]
                        dumpFileName = "RGB_"+str(selectedZProjectMethodName)+"_"+str(fileName)+"_"+str(impNumber)+"_"+str(serieNumber)
                    print(dumpFileName)
                    resultImagePlus.setCalibration(resizedImageCalibration)
                    saveFileImage(resultImagePlus, imagePlusFilePath, dumpSaveFilePath, dumpFileName, separator)
                    print("Done "+currentImagePlus.getTitle())
            print("End")
        sendValuesButton = JButton("Launch selected parameters on all images in directory", actionPerformed = globalPipeline)

        def shutDown(event):
            self.imageTuningDialogBox.dispose()
            print("End")
        cancelButton = JButton("Quit plugin", actionPerformed = shutDown)


        mainThumbnailItem.add(shownMainIconJLabel, imageIconGridBagConstraints)
        mainThumbnailItem.add(imageFileSelectorButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(imageFileSerieSelectorButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(zProjectMethodButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(zDepthButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(savePathButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(sendValuesButton, buttonsGridBagConstraints)
        mainThumbnailItem.add(cancelButton, buttonsGridBagConstraints)
        return mainThumbnailItem

    def createChannelThumbnail(self, channelTuner):
        channelThumbnailItem = JPanel(False)

        buttonsGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = GridBagConstraints.REMAINDER,
            gridheight = 1,
            weightx = 0.0,
            weighty = 0.0,
        )
        imageIconGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = 1,
            gridheight = 2,
            weightx = 0.0,
            weighty = 1.0
        )

        shownChannelIconJLabel = self.instanciateShownIcon(channelTuner)

        def openColorChooser(event):
            channelTuner.openColorChooser(event)
            #self.setShownIcon(channelTuner, shownChannelIconJLabel)
            self.imageSelector.refreshShownIconImage()
            #if self.imageSelector.selectedOperation == "Make Montage":
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.refreshShownIconImage()
            self.refreshAllIcons()
        channelLutColorSelectorButton = JButton("Channel Color", actionPerformed = openColorChooser)

        def openLutChooser(event):
            channelTuner.openLutChooser(event)
            #self.setShownIcon(channelTuner, shownChannelIconJLabel)
            self.imageSelector.refreshShownIconImage()
            #if self.imageSelector.selectedOperation == "Make Montage":
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.refreshShownIconImage()
            self.refreshAllIcons()
        channelLutCustomLUTSelectorButton = JButton("Select custom LUT", actionPerformed = openLutChooser)

        def openPixelBoundaryValuesTuner(event):
            channelTuner.openPixelBoundaryValuesTuner(event)
            #self.setShownIcon(channelTuner, shownChannelIconJLabel)
            self.imageSelector.refreshShownIconImage()
            #if self.imageSelector.selectedOperation == "Make Montage":
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.refreshShownIconImage()
            self.refreshAllIcons()
        channelPixelBoundaryValuesTunerButton = JButton("Tune Min/Max pixel values", actionPerformed = openPixelBoundaryValuesTuner)

        def openGammaCorrectionTuner(event):
            channelTuner.openGammaCorrectionTuner(event)
            #self.setShownIcon(channelTuner, shownChannelIconJLabel)
            self.imageSelector.refreshShownIconImage()
            #if self.imageSelector.selectedOperation == "Make Montage":
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.refreshShownIconImage()
            self.refreshAllIcons()
        channelGammaCorrectionValuesTunerButton = JButton("Set Gamma correction", actionPerformed = openGammaCorrectionTuner)

        channelThumbnailItem.add(shownChannelIconJLabel, imageIconGridBagConstraints)
        channelThumbnailItem.add(channelLutColorSelectorButton, buttonsGridBagConstraints)
        channelThumbnailItem.add(channelLutCustomLUTSelectorButton, buttonsGridBagConstraints)
        channelThumbnailItem.add(channelPixelBoundaryValuesTunerButton, buttonsGridBagConstraints)
        channelThumbnailItem.add(channelGammaCorrectionValuesTunerButton, buttonsGridBagConstraints)
        return channelThumbnailItem

    def createResultThumbnail(self):
        if self.imageSelector.selectedOperation == "Make Montage":
            resultThumbnail = self.createMontageThumbnail()
        if self.imageSelector.selectedOperation == "Make Composite":
            resultThumbnail = self.createCompositeThumbnail()
        return resultThumbnail

    def createMontageThumbnail(self):
        montageThumbnailItem = JPanel(False)
        centerButtonsGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = GridBagConstraints.REMAINDER,
            gridheight = 1,
            weightx = 0.0,
            weighty = 0.0,
        )
        imageIconGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = 1,
            gridheight = 2,
            weightx = 0.0,
            weighty = 1.0
        )

        currentStateDictionary = self.getLoadedImages()
        currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
        resultTuner = currentlySelectedImageSerie["ResultTuner"]
        shownMontageIconJLabel = self.instanciateShownIcon(resultTuner)

        def openPixelSizeChangerWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openPixelSizeChangerWindow(event)
        pixelSizeChangerTunerButton = JButton("Modifier reglage taille pixel", actionPerformed = openPixelSizeChangerWindow)

        def openResizeFactorEntryWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openResizeFactorEntryWindow(event)
        resizeFactorTunerButton = JButton("Coefficient de dimensionnement", actionPerformed = openResizeFactorEntryWindow)

        def openNumberRowColumnsWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openNumberRowColumnsWindow(event)
            self.setShownIcon(resultTuner, shownMontageIconJLabel)
            #self.refreshAllIcons()
        montageParametersTunerButton = JButton("Nombre de lignes/colonnes", actionPerformed = openNumberRowColumnsWindow)

        def openImageAssignatorWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openImageAssignatorWindow(event)
            self.setShownIcon(resultTuner, shownMontageIconJLabel)
            #self.refreshAllIcons()
        imageAssignatorButton = JButton("Assigner les images", actionPerformed = openImageAssignatorWindow)

        montageThumbnailItem.add(shownMontageIconJLabel, imageIconGridBagConstraints)
        montageThumbnailItem.add(resizeFactorTunerButton, centerButtonsGridBagConstraints)
        montageThumbnailItem.add(pixelSizeChangerTunerButton, centerButtonsGridBagConstraints)
        montageThumbnailItem.add(montageParametersTunerButton, centerButtonsGridBagConstraints)
        montageThumbnailItem.add(imageAssignatorButton, centerButtonsGridBagConstraints)
        return montageThumbnailItem

    def createCompositeThumbnail(self):
        compositeThumbnailItem = JPanel(False)
        buttonsGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = GridBagConstraints.REMAINDER,
            gridheight = 1,
            weightx = 0.0,
            weighty = 0.0,
        )
        #buttonsGridBagConstraints.insets.left = 5
        #buttonsGridBagConstraints.insets.right = 5
        imageIconGridBagConstraints = GridBagConstraints(
            gridx = GridBagConstraints.RELATIVE,
            gridy = GridBagConstraints.RELATIVE,
            fill = GridBagConstraints.BOTH,
            ipadx = 0,
            ipady = 0,
            insets = Insets(0,0,0,0),
            anchor = GridBagConstraints.CENTER,
            gridwidth = 1,
            gridheight = 2,
            weightx = 0.0,
            weighty = 1.0
        )

        currentStateDictionary = self.getLoadedImages()
        currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
        resultTuner = currentlySelectedImageSerie["ResultTuner"]
        shownCompositeIconJLabel = self.instanciateShownIcon(resultTuner)

        def openPixelSizeChangerWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openPixelSizeChangerWindow(event)
        pixelSizeChangerTunerButton = JButton("Modifier reglage taille pixel", actionPerformed = openPixelSizeChangerWindow)

        def openResizeFactorEntryWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openResizeFactorEntryWindow(event)
        resizeFactorTunerButton = JButton("Coefficient de dimensionnement", actionPerformed = openResizeFactorEntryWindow)

        def openImageTypeWindow(event):
            currentStateDictionary = self.getLoadedImages()
            currentlySelectedImageSerie = currentStateDictionary[str(self.imageSelector.getSelectedFile())]["Serie "+str(self.imageSelector.getSelectedSerie())]
            resultTuner = currentlySelectedImageSerie["ResultTuner"]
            resultTuner.openImageTypeWindow(event)
            self.setShownIcon(resultTuner, shownCompositeIconJLabel)
        imageTypeButton = JButton("Select type of result image", actionPerformed = openImageTypeWindow)

        compositeThumbnailItem.add(shownCompositeIconJLabel, imageIconGridBagConstraints)
        compositeThumbnailItem.add(resizeFactorTunerButton, buttonsGridBagConstraints)
        compositeThumbnailItem.add(pixelSizeChangerTunerButton, buttonsGridBagConstraints)
        compositeThumbnailItem.add(imageTypeButton, buttonsGridBagConstraints)
        return compositeThumbnailItem


#---------------------------------------------------------------------------------------#
#---------------------------Fonctions de traitement d'image-----------------------------#
#---------------------------------------------------------------------------------------#

def returnBufferedCalculatedMatrixFromImagePlus(imagePlus): #unused
    #zDepthForChannel = imagePlus.getNSlices() #Profondeur Z
    imageWidth = imagePlus.getWidth(); #Largeur de l'image
    imageHeight = imagePlus.getHeight(); #Hauteur de l'image
    imageBuffer = clij2_instance.push(imagePlus)
    newBufferedImageMatrix = clij2_instance.create(Long(imageHeight, imageWidth, 1)) #, NativeTypeEnum.Float
    pass


#----------------Z-PROJECTION FUNCTIONS----------------

def makeZProjectOnSingleChannel(channelImage, methodName): ####---MY Z-PROJECT ALGORITHM IS HERE---######
    """
    Mon algorithme perso pour faire un montage à partir d'une pile d'images en niveaux de gris (un canal).
    """
    imageWidth = channelImage.getWidth()
    imageHeight = channelImage.getHeight()
    bitDepth = channelImage.getBitDepth()

    def median(listOfNumbers):
    	listOfNumbers.sort()
    	middle = len(listOfNumbers)/2
    	if ((len(listOfNumbers) & 1) == 0):
    		return int((listOfNumbers[middle-1] + listOfNumbers[middle])/2)
    	else:
    		return listOfNumbers[middle]

    def sd(listOfNumbers):
        average = sum(listOfNumbers)/len(listOfNumbers)
        squaredValuesMinusAverage = []
        for value in listOfNumbers:
            valueMinusAverage = value - average
            squaredValueMinusAverage = valueMinusAverage**2
            squaredValuesMinusAverage.append(squaredValueMinusAverage)
        squaredDeviation = math.sqrt(sum(squaredValuesMinusAverage)/len(listOfNumbers))
        return squaredDeviation

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
        if methodName == "sd":
            globalPixelValue = int(sd(pixelValuesForEachChannel))

        if globalPixelValue > (2**bitDepth)-1: #Correction pour éviter les artefacts visuels liés au dépassement de la valeur max possible (revient à 0 sinon)
            globalPixelValue = (2**bitDepth)-1

        newZProjectChannelImageProcessor.set(indice, globalPixelValue)
    return newZProjectChannelImage

def makeZProject(imagePlus, methodName): #Cette fonction fait le Z-Project sur les 3 canaux. Utilise l'algo précédent.
    """
    Cette fonction fait le Z-Project sur les 3 canaux. Utilise l'algo précédent. Cette fonction devrait être interchangeable avec la fonction test:
        "makeImageJZProject(imagePlus, methodName)"
    """
    zProjectedImageStack = ImageStack()
    numberOfChannels = imagePlus.getNChannels() #Nombre de canaux
    numberOfTimeFrames = imagePlus.getNFrames() #Nombre de "time-points". Penser à les gérer.
    stackedImages = imagePlus.getStack()
    totalNumberOfImages = stackedImages.getSize() #Profondeur Z * Nombre de canaux * numberOfTimeFrames

    arrayOfChannels = separateByChannels(imagePlus)
    channelNumber = 0
    for channelImagePlus in arrayOfChannels:
        zProjectedChannelImagePlus = makeZProjectOnSingleChannel(channelImagePlus, methodName)
        zProjectedChannelImageProcessor = zProjectedChannelImagePlus.getProcessor()
        zProjectedChannelTitle = String("Channel "+str(channelNumber+1)+", Z-Project "+str(methodName))
        zProjectedImageStack.addSlice(zProjectedChannelTitle, zProjectedChannelImageProcessor)
        channelNumber += 1

    zProjectedImageTitle = String("Z-Project "+str(methodName))
    #zProjectedImagePlus = ImagePlus(zProjectedImageTitle, zProjectedImageStack)
    zProjectedImagePlus = ImagePlus()
    zProjectedImagePlus.setTitle(zProjectedImageTitle)
    zProjectedImagePlus.setStack(zProjectedImageStack, numberOfChannels, 1, numberOfTimeFrames) #1 seule slice car c'est une projection
    #zProjectedImagePlus.show()
    return zProjectedImagePlus

def makeImageJZProject(imagePlus, methodName): #Fonction de test utilisant l'API ZProjector d'ImageJ/Fiji.
    """
    J'a bricolé ici une fonction utilisant l'API ZProjector d'ImageJ/Fiji. Juste pour tester, je ne m'en sers pas en temps normal.

    Voir:
    https://github.com/imagej/ImageJA/blob/master/src/main/java/ij/plugin/ZProjector.java
    https://imagej.nih.gov/ij/developer/api/ij/plugin/ZProjector.html
    https://imagej.net/Z-functions

    Il existe dans le ZProjector une fonction alternative prenant un Z de départ et un Z de fin.
    """

    zProjectedImageStack = ZProjector.run(imagePlus, methodName) #Retourne un stack de canaux. Chaque canal correspond à la projection sur Z. Ne donne qu'une superposition des canaux pour une image d'une seule profondeur.
    zProjectedImagePlus = ImagePlus("Z-Project "+str(methodName), zProjectedImageStack)
    return zProjectedImagePlus

def makeZProjectOnSingleChannel_CLIJ2(channelImagePlus, methodName, clij2_instance): #unused
    """
    #https://clij.github.io/clij2-docs/api_intro

    # convert ImageJ image to CL images (ready for the GPU)
    inputCLBuffer = clij2.push(imp);
    outputCLBuffer = clij2.create(inputCLBuffer); # allocate memory for result image

    # downsample the image stack using ClearCL / OpenCL
    clij2.execute(DownsampleXYbyHalfTask, "kernels/downsampling.cl", "downsample_xy_by_half_nearest", inputCLBuffer.getDimensions(), inputCLBuffer.getDimensions(), {"src":inputCLBuffer, "dst":outputCLBuffer});

    # convert the result back to imglib2 and show it
    result = clij2.pull(outputCLBuffer);
    result.show();

    # free memory on the GPU - needs to be done explicitly
    inputCLBuffer.close();
    outputCLBuffer.close();
    """
    # convert ImageJ image to CL images (ready for the GPU)
    channelImageBuffer = clij2_instance.push(channelImagePlus);
    resultImageBuffer = clij2_instance.create(channelImageBuffer); # allocate memory for result image

    if methodName == "max":
        clij2_instance.maximumZProjection(channelImageBuffer, resultImageBuffer) #differnce with argMaximumZProjection?
    if methodName == "min":
        clij2_instance.minimumZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "sum":
        clij2_instance.sumZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "average":
        clij2_instance.meanZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "median":
        clij2_instance.medianZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "sd":
        clij2_instance.standardDeviationZProjection(channelImageBuffer, resultImageBuffer)

    # convert the result back to imglib2
    newZProjectChannelImagePlus = clij2_instance.pull(resultImageBuffer)

    # free memory on the GPU - needs to be done explicitly
    channelImageBuffer.close()
    resultImageBuffer.close()

    return newZProjectChannelImagePlus

def makeZProject_CLIJ2(imageBuffer, methodName, clij2_instance):
    if methodName == "max":
        clij2_instance.maximumZProjection(channelImageBuffer, resultImageBuffer) #differnce with argMaximumZProjection?
    if methodName == "min":
        clij2_instance.minimumZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "sum":
        clij2_instance.sumZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "average":
        clij2_instance.meanZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "median":
        clij2_instance.medianZProjection(channelImageBuffer, resultImageBuffer)
    if methodName == "sd":
        clij2_instance.standardDeviationZProjection(channelImageBuffer, resultImageBuffer)
    return resultImageBuffer


#----------------IMAGE CALCULUS FUNCTIONS----------------

def gammaCorrectionOperation(pixelValue, A_factor, gamma_factor):
    """
    Voir:
    https://en.wikipedia.org/wiki/Gamma_correction
    https://fr.wikipedia.org/wiki/Gamma_(photographie)
    https://www.cambridgeincolour.com/tutorials/gamma-correction.htm
    https://forum.image.sc/t/gamma-adjustment-in-brightness-contrast-window/768/

    Ma formule de base:
    #gammaCorrectedPixelValue = A_factor*(pixelValue**gamma_factor)

    Si on imagine qu'un ajustement gamma est applqué lors de la génération de l'image,
    on peut imaginer qu'une correction est une tentative pour "inverser" l'impact
    de cette altération de cette façon:
    #gammaCorrectedPixelValue = (pixelValue**(1/gamma_factor))/A_factor
    """
    gammaCorrectedPixelValue = (pixelValue**(1/gamma_factor))/A_factor
    integerGammaCorrectedLevelValue = int(gammaCorrectedPixelValue)
    return integerGammaCorrectedLevelValue

def calculateRealPixelValue(originalChannelImageProcessor, maxPossibleTargetImagePixelValue, integerRawLevelValue, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor):
    originalImageBitDepth = originalChannelImageProcessor.getBitDepth()
    maxPossibleValue = (2**originalImageBitDepth)-1
    maxShownPixelValue = int(originalChannelImageProcessor.getMax())
    #if maxShownPixelValue == 0: #???
        #maxShownPixelValue = maxPossibleValue #???
    minShownPixelValue = int(originalChannelImageProcessor.getMin())
    correctedLevelValue = maxPossibleTargetImagePixelValue*(integerRawLevelValue-minShownPixelValue)/(maxShownPixelValue-minShownPixelValue)
    correctedLevelValue = gammaCorrectionOperation(correctedLevelValue, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
    integerCorrectedLevelValue = int(correctedLevelValue)
    if integerCorrectedLevelValue < 0: #Correction pour le dépassement de liste. Vérifier si l'approche est correcte.
        integerCorrectedLevelValue = 0
    if integerCorrectedLevelValue > maxPossibleTargetImagePixelValue: #Correction pour le dépassement de liste. Vérifier si l'approche est correcte.
        integerCorrectedLevelValue = maxPossibleTargetImagePixelValue
    return integerCorrectedLevelValue

def calculateTargetImage_CLIJ2(originalChannelImagePlus, minOriginalImageShownPixelValue, maxOriginalImageShownPixelValue, maxPossibleTargetImagePixelValue, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, clij2_instance):
    #Homologue de calculateRealPixelValue mais pour l'image entière et sur GPU.
    #Explication pour les float: https://stackoverflow.com/questions/10768724/why-does-python-return-0-for-simple-division-calculation
    A_pixel_equation_coefficient = float(maxPossibleTargetImagePixelValue)/(float(maxOriginalImageShownPixelValue)-float(minOriginalImageShownPixelValue))
    B_pixel_equation_factor = -1.0*(float(maxPossibleTargetImagePixelValue)*float(minOriginalImageShownPixelValue))/(float(maxOriginalImageShownPixelValue)-float(minOriginalImageShownPixelValue))
    print("A_pixel_equation_coefficient: "+str(A_pixel_equation_coefficient)+" B_pixel_equation_factor: "+str(B_pixel_equation_factor))
    originalChannelImageBuffer = clij2_instance.push(originalChannelImagePlus)
    tempBuffer1 = clij2_instance.create(originalChannelImageBuffer)
    tempBuffer2 = clij2_instance.create(originalChannelImageBuffer)
    tempBuffer3 = clij2_instance.create(originalChannelImageBuffer)
    targetChannelImageBuffer = clij2_instance.create(originalChannelImageBuffer)
    clij2_instance.multiplyImageAndScalar(originalChannelImageBuffer, tempBuffer1, A_pixel_equation_coefficient)
    clij2_instance.addImageAndScalar(tempBuffer1, tempBuffer2, B_pixel_equation_factor)

    #Gamma correction
    clij2_instance.power(tempBuffer2, tempBuffer3, 1/gammaCorrection_gamma_power_factor)
    clij2_instance.multiplyImageAndScalar(tempBuffer3, targetChannelImageBuffer, 1/gammaCorrection_A_linear_factor)

    targetChannelImagePlus = clij2_instance.pull(targetChannelImageBuffer)
    return targetChannelImagePlus

def calculateCorrectedMinMaxPixelValues(originalChannelImageProcessor, minvalue, maxvalue):
    originalImageBitDepth = originalChannelImageProcessor.getBitDepth()
    maxPossibleValue = int((2**originalImageBitDepth)-1)
    maxShownPixelValue = int(originalChannelImageProcessor.getMax())
    if maxShownPixelValue == 0:
        maxShownPixelValue = maxPossibleValue
    minShownPixelValue = int(originalChannelImageProcessor.getMin())
    correctedMinPixelValue = int(minShownPixelValue + minvalue*(maxShownPixelValue-minShownPixelValue)/maxPossibleValue)
    correctedMaxPixelValue = int(minShownPixelValue + maxvalue*(maxShownPixelValue-minShownPixelValue)/maxPossibleValue)

    return correctedMinPixelValue, correctedMaxPixelValue

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

def makeRedGreenBluePixel(leveledBlueValue, leveledGreenValue, leveledRedValue):
    leveledBitDepth = 8 #Image RGB: 24 bits = 3x8 bits
    pixelBlueValue = makeBluePixel(leveledBlueValue, leveledBitDepth)
    pixelGreenValue = makeGreenPixel(leveledGreenValue, leveledBitDepth)
    pixelRedValue = makeRedPixel(leveledRedValue, leveledBitDepth)
    colouredPixelValue = pixelBlueValue + pixelGreenValue + pixelRedValue
    colouredPixelValue = int(colouredPixelValue)
    return colouredPixelValue


#----------------GENERAL IMAGE PROCESSING FUNCTIONS----------------

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
    print("Separating by channels...")
    arrayOfChannels = []
    for channelNumber in range(0,numberOfChannels):
        channelStack = ImageStack(imageWidth, imageHeight)
        zDepthNumber = 1
        for imageNumber in range(channelNumber, totalNumberOfImages, numberOfChannels):
            sliceTitle = stackedImages.getSliceLabel(imageNumber+1)
            sliceProcessor = stackedImages.getProcessor(imageNumber+1)
            channelStack.addSlice(sliceTitle, sliceProcessor)
            zDepthNumber+=1
        channelTitle = String("Channel "+str(channelNumber+1))
        channelImagePlus = ImagePlus(channelTitle, channelStack)
        arrayOfChannels.append(channelImagePlus)
    print("Finished separating by channels")
    return arrayOfChannels

def makeChannelTuningPipeline(channelImagePlus, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedZProjectMethodName, selectedOperation):
    zDepthForChannel = channelImagePlus.getNSlices() #Profondeur Z
    imageWidth = channelImagePlus.getWidth(); #Largeur de l'image
    imageHeight = channelImagePlus.getHeight(); #Hauteur de l'image
    bitDepth = channelImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    targetImageBitDepth = 8
    maxPossibleTargetImagePixelValue = int((2**targetImageBitDepth)-1)

    channelImageProcessor = channelImagePlus.getProcessor()
    #correctedMinPixelValue, correctedMaxPixelValue = calculateCorrectedMinMaxPixelValues(channelImageProcessor, valeurPixelMinHistogram, valeurPixelMaxHistogram)
    correctedMinPixelValue = valeurPixelMinHistogram
    correctedMaxPixelValue = valeurPixelMaxHistogram
    channelImageProcessor.setMinAndMax(correctedMinPixelValue, correctedMaxPixelValue) #Ne pas confondre setHistogramRange() avec setMinAndMax() (voir doc)

    channelStackedImages = channelImagePlus.getStack()
    newPseudoColoredChannelStack = ImageStack(imageWidth, imageHeight)
    """
    if selectedLUT == "---No_custom_LUT---":
        newPseudoColoredChannelImageTitle = "LUTted "+str(selectedPseudoColor)+", Channel "+str(channelNumber)
    if selectedLUT != "---No_custom_LUT---":
        newPseudoColoredChannelImageTitle = "LUTted "+str(selectedLUT)+", Channel "+str(channelNumber)
    """
    newPseudoColoredChannelImageTitle = "Channel "+str(channelNumber)
    for zNumber in range(0, zDepthForChannel):
        zImageProcessor = channelStackedImages.getProcessor(zNumber+1)
        if selectedOperation == "Make Montage":
            newPseudoColoredChannelZImagePlus = IJ.createImage(str(newPseudoColoredChannelImageTitle)+", Z-Depth "+str(zNumber+1), "RGB Black", imageWidth, imageHeight, 1)
            newPseudoColoredChannelZImageProcessor = processorsTuningPipelineForRedGreenBlueChannelImages(zImageProcessor, newPseudoColoredChannelZImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedPseudoColor, selectedLUT, channelNumber, zNumber, selectedZProjectMethodName)
        if selectedOperation == "Make Composite":
            newPseudoColoredChannelZImagePlus = IJ.createImage(str(newPseudoColoredChannelImageTitle)+", Z-Depth "+str(zNumber+1), imageWidth, imageHeight, 1, bitDepth)
            newPseudoColoredChannelZImageProcessor = processorsTuningPipelineForGrayLevelChannelImages(zImageProcessor, newPseudoColoredChannelZImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedPseudoColor, selectedLUT, channelNumber, zNumber, selectedZProjectMethodName)
        newPseudoColoredChannelZImagePlus.setProcessor(newPseudoColoredChannelZImageProcessor)
        newPseudoColoredChannelStack.addSlice(newPseudoColoredChannelZImageProcessor)
    newPseudoColoredChannelImagePlus = ImagePlus(String(newPseudoColoredChannelImageTitle), newPseudoColoredChannelStack)

    return newPseudoColoredChannelImagePlus

def makeChannelTuningPipeline_CLIJ2(channelImagePlus, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedZProjectMethodName, selectedOperation, clij2_instance):
    #équivalent de processorsTuningPipelineForGrayLevelChannelImages(
    bitDepth = channelImagePlus.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    targetImageBitDepth = 8
    maxPossibleTargetImagePixelValue = int((2**targetImageBitDepth)-1)

    channelImageProcessor = channelImagePlus.getProcessor()
    #correctedMinPixelValue, correctedMaxPixelValue = calculateCorrectedMinMaxPixelValues(channelImageProcessor, valeurPixelMinHistogram, valeurPixelMaxHistogram)
    correctedMinPixelValue = valeurPixelMinHistogram
    correctedMaxPixelValue = valeurPixelMaxHistogram
    channelImageProcessor.setMinAndMax(correctedMinPixelValue, correctedMaxPixelValue) #Ne pas confondre setHistogramRange() avec setMinAndMax() (voir doc)

    newPseudoColoredChannelImagePlus = calculateTargetImage_CLIJ2(channelImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, maxPossibleTargetImagePixelValue, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, clij2_instance)
    newPseudoColoredChannelImageProcessor = newPseudoColoredChannelImagePlus.getProcessor()
    if selectedLUT != "---No_custom_LUT---":
        currentLUT = LutLoader.openLut(lutPath+selectedLUT)
    if selectedLUT == "---No_custom_LUT---":
        currentLUT = LUT.createLutFromColor(selectedPseudoColor)

    newPseudoColoredChannelImageProcessor.setLut(currentLUT)

    return newPseudoColoredChannelImagePlus

def makeTunedChannelImages(imagePlus, channelTuners):
    zProjectChannels = separateByChannels(imagePlus)
    zProjectedTunedImages = []
    channelNumber = 0
    for zProjectChannelImage in zProjectChannels:
        channelTuner = channelTuners[channelNumber]
        selectedPseudoColor = channelTuner.getSelectedPseudoColor()
        selectedLUT = channelTuner.getSelectedCustomLUT()
        valeurPixelMinHistogram = channelTuner.getSelectedMinPixelValue()
        valeurPixelMaxHistogram = channelTuner.getSelectedMaxPixelValue()
        selectedZProjectMethodName = channelTuner.getSelectedZProjectMethodName()
        gammaCorrection_A_linear_factor = channelTuner.getGamma_A_LinearFactor()
        gammaCorrection_gamma_power_factor = channelTuner.getGamma_gamma_PowerFactor()
        selectedOperation = channelTuner.getSelectedOperation()
        valeurSelectionBooleanCLIJ = channelTuner.getCLIJboolean()
        clij2_instance = channelTuner.getCLIJinstance()

        if valeurSelectionBooleanCLIJ == False:
            newPseudoColoredChannelImagePlus = makeChannelTuningPipeline(zProjectChannelImage, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedZProjectMethodName, selectedOperation)
        if valeurSelectionBooleanCLIJ == True:
            newPseudoColoredChannelImagePlus = makeChannelTuningPipeline_CLIJ2(zProjectChannelImage, channelNumber, selectedPseudoColor, selectedLUT, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedZProjectMethodName, selectedOperation, clij2_instance)

        zProjectedTunedImages.append(newPseudoColoredChannelImagePlus)
        channelNumber+=1
    return zProjectedTunedImages


#----------------RGB IMAGE PROCESSING FUNCTIONS----------------

def processorsTuningPipelineForRedGreenBlueChannelImages(channelImageProcessor, newPseudoColoredChannelImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedPseudoColor, selectedLUT, channelNumber, selectedZDepth, selectedZProjectMethodName):
    lutPath = IJ.getDirectory("luts")
    #print(str(lutPath))
    newPseudoColoredChannelImageProcessor = newPseudoColoredChannelImagePlus.getProcessor()
    imageHeight = newPseudoColoredChannelImageProcessor.getHeight()
    imageWidth = newPseudoColoredChannelImageProcessor.getWidth()

    imageName = "Channel "+str(channelNumber)+" - Z-Depth: "+str(selectedZDepth)+" - Z-Project: "+str(selectedZProjectMethodName)+", Color: "+str(selectedPseudoColor)+", LUT: "+str(selectedLUT)
    #print(imageName)
    newPseudoColoredChannelImagePlus.setTitle(String(imageName))
    if selectedLUT != "---No_custom_LUT---":
        customLUT = LutLoader.openLut(lutPath+selectedLUT)
        customLUTbytes = customLUT.getBytes()
        #print(customLUTbytes)
        #print(len(customLUTbytes))

        def divide_chunks(l, n):
            """
            Provient de: https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
            """
            # looping till length l
            for i in range(0, len(l), n):
                yield l[i:i + n]

        leveledBitDepth = 8
        maxGrayValue = int((2**leveledBitDepth)-1)
        customLUTbytes_ordered_by_color = list(divide_chunks(customLUTbytes, 256)) #LUT: 768 valeurs = 256 x 3
        customLUT_redValues = customLUTbytes_ordered_by_color[0]
        customLUT_greenValues = customLUTbytes_ordered_by_color[1]
        customLUT_blueValues = customLUTbytes_ordered_by_color[2]
        for indice in range(imageWidth*imageHeight):
            integerGrayLevel = channelImageProcessor.get(indice)
            leveledGrayValue = calculateRealPixelValue(channelImageProcessor, maxGrayValue, integerGrayLevel, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
            leveledBlueValue = customLUT_blueValues[leveledGrayValue]
            leveledGreenValue = customLUT_greenValues[leveledGrayValue]
            leveledRedValue = customLUT_redValues[leveledGrayValue]
            colouredPixelValue = makeRedGreenBluePixel(leveledBlueValue, leveledGreenValue, leveledRedValue)
            newPseudoColoredChannelImageProcessor.set(indice, colouredPixelValue)

    if selectedLUT == "---No_custom_LUT---":
        #createLutFromColor(java.awt.Color color) - Creates a color LUT from a Color.
        maxRedValue = selectedPseudoColor.getRed()
        maxGreenValue = selectedPseudoColor.getGreen()
        maxBlueValue = selectedPseudoColor.getBlue()
        for indice in range(imageWidth*imageHeight):
            integerGrayLevel = channelImageProcessor.get(indice)
            leveledBlueValue = calculateRealPixelValue(channelImageProcessor, maxBlueValue, integerGrayLevel, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
            leveledGreenValue = calculateRealPixelValue(channelImageProcessor, maxGreenValue, integerGrayLevel, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
            leveledRedValue = calculateRealPixelValue(channelImageProcessor, maxRedValue, integerGrayLevel, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
            colouredPixelValue = makeRedGreenBluePixel(leveledBlueValue, leveledGreenValue, leveledRedValue)
            newPseudoColoredChannelImageProcessor.set(indice, colouredPixelValue)

    return newPseudoColoredChannelImageProcessor

def makeFusedChannelsRedGreenBlueImage(arrayOfImages):
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


#----------------RGB MONTAGE PROCESSING FUNCTIONS----------------

def makeDictionaryOfViewableImages(zProjectedTunedImages, fusedChannelsImage): #Utilsée pour créer le dictionnaire des images sélectionnables dans les listes déroulantes
    """
    Utilsée pour créer le dictionnaire des images sélectionnables dans les listes déroulantes. Pas de rôle direct dans le traitement d'images.
    """
    dictionaryOfCurrentImages = {}
    for channelImage in zProjectedTunedImages:
        channelImageTitle = channelImage.getTitle()
        dictionaryOfCurrentImages[str(channelImageTitle)] = channelImage
    fusedImageTitle = fusedChannelsImage.getTitle()
    dictionaryOfCurrentImages[str(fusedImageTitle)] = fusedChannelsImage
    #Make empty image
    defaultMaxZDepth = fusedChannelsImage.getNSlices()
    defaultWidth = fusedChannelsImage.getWidth()
    defaultHeight = fusedChannelsImage.getHeight()
    newEmptyImageStack = ImageStack(defaultWidth, defaultHeight)
    newEmptyImage = IJ.createImage("---Empty---", "RGB Black", defaultWidth, defaultHeight, 1)
    for zDepth in range(0, defaultMaxZDepth):
        newEmptyImageProcessor = newEmptyImage.getProcessor()
        newEmptyImageStack.addSlice(newEmptyImageProcessor)
    fullEmptyImage = ImagePlus("Empty Image", newEmptyImageStack)
    dictionaryOfCurrentImages["---Empty---"] = fullEmptyImage
    return dictionaryOfCurrentImages

def makeArrayOfPreMontageImages(listOfAssignedImages, dictionaryOfAssignableImages):
    #print("listOfAssignedImages: ", listOfAssignedImages)
    #print("dictionaryOfAssignableImages: ", dictionaryOfAssignableImages)
    arrayOfSelectedImagesPlus = []

    for assignedImageName in listOfAssignedImages:
        for dictKey in dictionaryOfAssignableImages.keys():
            if str(assignedImageName) == str(dictKey):
                arrayOfSelectedImagesPlus.append(dictionaryOfAssignableImages[dictKey])

    maxZDepth = 0
    for dictKey in dictionaryOfAssignableImages.keys():
        currentZDepth = dictionaryOfAssignableImages[dictKey].getNSlices()
        if currentZDepth > maxZDepth:
            maxZDepth = currentZDepth

    zDepthPreMontageImages = []
    #print("self.maxZDepth: ", maxZDepth)
    for zDepth in range(0, maxZDepth):
        newOneZDepthStack = ImageStack()
        for image in arrayOfSelectedImagesPlus:
            currentMaxZDepth = image.getNSlices()
            currentWidth = image.getWidth()
            currentHeight = image.getHeight()
            newEmptyImage = IJ.createImage("---Empty---", "RGB Black", currentWidth, currentHeight, 1)
            imageStack = image.getStack()
            if zDepth+1 <= currentMaxZDepth:
                selectedSliceProcessor = imageStack.getProcessor(zDepth+1)
                newOneZDepthStack.addSlice(selectedSliceProcessor)
            if zDepth+1 > currentMaxZDepth:
                selectedSliceProcessor = newEmptyImage.getProcessor()
                newOneZDepthStack.addSlice(selectedSliceProcessor)
        newOneZDepthImage = ImagePlus("Pre-Montage, Z-Depth: "+str(zDepth+1), newOneZDepthStack)
        #newOneZDepthImage.show()
        zDepthPreMontageImages.append(newOneZDepthImage)
    #print(zDepthPreMontageImages)
    return zDepthPreMontageImages

def stackMontages(arrayOfDisplayableStacks, numberOfColumns, numberOfRows, valeurSelectionBooleanCLIJ, clij2_instance):
    depthStack = ImageStack()
    for stackImp in arrayOfDisplayableStacks:
        newMontageImage, montageWidth, montageHeight = makeMontage(stackImp, numberOfColumns, numberOfRows, valeurSelectionBooleanCLIJ, clij2_instance)
        newMontageImageProcessor = newMontageImage.getProcessor()
        depthStack.addSlice(newMontageImageProcessor)
    depthStackImp = ImagePlus("Montage Z-Project", depthStack)
    return depthStackImp

def makeMontage(stackImp, numberOfColumns, numberOfRows, valeurSelectionBooleanCLIJ, clij2_instance):
    if valeurSelectionBooleanCLIJ == False:
        newMontageImage, montageWidth, montageHeight = makeMontage_no_GPU(stackImp, numberOfColumns, numberOfRows)
    if valeurSelectionBooleanCLIJ == True:
        newMontageImage, montageWidth, montageHeight = makeMontage_CLIJ2(stackImp, numberOfColumns, numberOfRows, clij2_instance)
    return newMontageImage, montageWidth, montageHeight

def makeMontage_no_GPU(stackImp, numberOfColumns, numberOfRows): #Mon algorithme perso pour faire un montage à partir d'une pile d'images.
    """
    Mon algorithme perso pour faire un montage à partir d'une pile d'images.
    Moins élaboré que la fonction de l'API d'ImageJ/Fiji MontageMaker (https://imagej.nih.gov/ij/developer/api/ij/plugin/MontageMaker.html):
        "makeMontage2(ImagePlus imp, int columns, int rows, double scale, int first, int last, int inc, int borderWidth, boolean labels)"
    car ne prend pas en compte les tailles des marges, l'image de début et l'image de fin ou le redimensionnement (je m'occupe de ça plus en amont).
    Encore une fois, j'ai découvert l'API MontageMaker très tard (et je ne l'ai pas testée), et ce que j'avais marchait très bien, donc je suis resté dans mon truc.
    """
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

def makeMontagePipeline(imagePlus, channelTuners, montageTuner):
    """
    Pipeline de montage proprement dit.
    ImageJ/Fiji propose une API pour le faire (https://imagej.nih.gov/ij/developer/api/ij/plugin/MontageMaker.html) mais je l'ai découverte très tardivement.
    J'ai préféré rester sur ma solution, qui me semble pas mal: au final, seul le redimensionnement des images (ci-dessus) influera sur la rapidité.
    """
    numberOfColumns = montageTuner.getNumberOfColumns()
    numberOfRows = montageTuner.getNumberOfRows()
    valeurSelectionBooleanCLIJ = montageTuner.getCLIJboolean()
    clij2_instance = montageTuner.getCLIJinstance()

    zProjectedTunedImages = makeTunedChannelImages(imagePlus, channelTuners)
    if valeurSelectionBooleanCLIJ == False:
        fusedChannelsImage = makeFusedChannelsRedGreenBlueImage(zProjectedTunedImages)
    if valeurSelectionBooleanCLIJ == True:
        fusedChannelsImage = makeFusedChannels_CLIJ2(zProjectedTunedImages)

    dictionaryOfCurrentImages = makeDictionaryOfViewableImages(zProjectedTunedImages, fusedChannelsImage)
    zDepthPreMontageImagesArray = makeArrayOfPreMontageImages(montageTuner.getListOfAssignedImages(), dictionaryOfCurrentImages)
    montageImp = stackMontages(zDepthPreMontageImagesArray, numberOfColumns, numberOfRows, valeurSelectionBooleanCLIJ, clij2_instance)

    return montageImp

def makeMontage_CLIJ2(stackImp, numberOfColumns, numberOfRows, clij2_instance): #Partially dysfunctional because CLIJ2 doesn't work on 24bit (3x8bit) RGB images
    #https://clij.github.io/clij2-docs/md/crop_and_paste/
    bitDepth = stackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    imageWidth = stackImp.getWidth(); #Largeur de l'image
    imageHeight = stackImp.getHeight(); #Hauteur de l'image
    numberOfSlices = stackImp.getNSlices() #Nombre d'images du stack
    montageWidth = imageWidth*int(numberOfColumns)
    montageHeight = imageHeight*int(numberOfRows)

    # convert ImageJ image to CL images (ready for the GPU)
    stackImpBuffer = clij2_instance.push(stackImp);
    newMontageImageBuffer = clij2_instance.create2D("new2D", montageWidth, montageHeight, bitDepth); # allocate memory for result image

    yMontage = 0
    xMontage = 0
    newXOrigin = 0
    newYOrigin = 0
    #processorBuffers = []
    for imageNumber in range(0,numberOfSlices):
        vignetteImagePlus = stackImp.createImagePlus()
        vignetteImageProcessor = stack.getProcessor(imageNumber+1)
        vignetteImagePlus.setProcessor(vignetteImageProcessor)
        vignetteImageBuffer = clij2_instance.push(vignetteImagePlus);
        #processorBuffers.append(vignetteImageBuffer)

        #for rowNumber in range(numberOfRows):
            #yMontage = (newYOrigin)+imageWidth
            #for columnNumber in range(numberOfColumns):
                #xMontage = (newXOrigin)+imageHeight
        if newXOrigin*newYOrigin >= montageWidth*montageHeight:
            break
        if newXOrigin < montageWidth:# and newXOrigin != 0:
            newXOrigin = newXOrigin+imageWidth
            newYOrigin = newYOrigin
        if newXOrigin == montageWidth:
            newXOrigin = 0
            newYOrigin = newYOrigin+imageHeight
        clij2_instance.paste2D(vignetteImageBuffer, newMontageImageBuffer, newXOrigin, newYOrigin)

    # convert the result back to imglib2
    newMontageImagePlus = clij2_instance.pull(newMontageImageBuffer)

    # free memory on the GPU - needs to be done explicitly
    stackImpBuffer.close()
    newMontageImageBuffer.close()

    return newMontageImagePlus, montageWidth, montageHeight

def makeFusedChannels_CLIJ2(listOfImages, clij2_instance):
    """
    Ajoute récursivement les images pour contourner la limite de 2 images des fonctions de CLIJ2.
    Echoue à faire un composite, fait juste un merge. Peut-être pour montages en niveaux de gris...
    """
    if len(listOfImages) == 1:
        leveledCompositeImage = listOfImages[0]
        leveledCompositeImage.setTitle("Fused Image")
        return leveledCompositeImage
    if len(listOfImages) > 1:
        image1 = clij2_instance.push(listOfImages.pop(0)) #listOfImages[0]
        image2 = clij2_instance.push(listOfImages.pop(0)) #listOfImages[1]
        sumOfImages = clij2_instance.create(image1)
        clij2_instance.addImages(image1, image2, sumOfImages)
        resultImagePlus = clij2_instance.pull(sumOfImages)
        listOfImages.append(resultImagePlus)
        return makeFusedChannels_CLIJ2(listOfImages, clij2_instance)


#----------------COMPOSITE IMAGE PROCESSING FUNCTIONS----------------

def processorsTuningPipelineForGrayLevelChannelImages(channelImageProcessor, newPseudoColoredChannelImagePlus, valeurPixelMinHistogram, valeurPixelMaxHistogram, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor, selectedPseudoColor, selectedLUT, channelNumber, selectedZDepth, selectedZProjectMethodName):
    newPseudoColoredChannelImageProcessor = newPseudoColoredChannelImagePlus.getProcessor()
    imageHeight = newPseudoColoredChannelImageProcessor.getHeight()
    imageWidth = newPseudoColoredChannelImageProcessor.getWidth()

    bitDepth = newPseudoColoredChannelImageProcessor.getBitDepth()
    maxGrayValue = int((2**bitDepth)-1)

    imageName = "Channel "+str(channelNumber)+" - Z-Depth: "+str(selectedZDepth)+" - Z-Project: "+str(selectedZProjectMethodName)+", Color: "+str(selectedPseudoColor)+", LUT: "+str(selectedLUT)
    #print(imageName)
    newPseudoColoredChannelImagePlus.setTitle(String(imageName))

    for indice in range(imageWidth*imageHeight):
        integerGrayLevel = channelImageProcessor.get(indice)
        leveledGrayValue = calculateRealPixelValue(channelImageProcessor, maxGrayValue, integerGrayLevel, gammaCorrection_A_linear_factor, gammaCorrection_gamma_power_factor)
        newPseudoColoredChannelImageProcessor.set(indice, leveledGrayValue)

    if selectedLUT != "---No_custom_LUT---":
        currentLUT = LutLoader.openLut(lutPath+selectedLUT)
    if selectedLUT == "---No_custom_LUT---":
        currentLUT = LUT.createLutFromColor(selectedPseudoColor)

    newPseudoColoredChannelImageProcessor.setLut(currentLUT)
    return newPseudoColoredChannelImageProcessor

def makeFusedChannelsCompositeImage(arrayOfImages):
    leveledCompositeImage = RGBStackMerge.mergeChannels(arrayOfImages, True) #True pour garder les images sources
    leveledCompositeImage.setTitle("Fused Image")
    return leveledCompositeImage

def finalizeCompositeImagePlus(imagePlusComposite, compositeTuner):
    """
    Le type d'image peut prendre plusieurs valeurs (voir l'API officielle):
    0: COLOR; 1: COMPOSITE; 2: COLOR; 3: GRAYSCALE; 4: TRANSPARENT (non-implemented); 5: TRANSPARENT? (non-implemented); 6: TRANSPARENT? (non-implemented)...

    Voir: https://github.com/imagej/imagej1/blob/master/ij/CompositeImage.java
    """
    imageType = compositeTuner.getImageType()
    if imageType == "Color":
        typeValue = 2
    if imageType == "Composite":
        typeValue = 1
    if imageType == "Grayscale":
        typeValue = 3

    #imagePlusComposite.setMode(typeValue)
    imagePlusComposite.setDisplayMode(typeValue)

    return imagePlusComposite

def makeCompositePipeline(imagePlus, channelTuners, compositeTuner):
    """
    Pipeline de transformation en Composite.
    """
    valeurSelectionBooleanCLIJ = compositeTuner.getCLIJboolean()
    clij2_instance = compositeTuner.getCLIJinstance()

    zProjectedTunedImages = makeTunedChannelImages(imagePlus, channelTuners)
    compositeFusedChannelsImage = makeFusedChannelsCompositeImage(zProjectedTunedImages)
    imagePlusComposite = finalizeCompositeImagePlus(compositeFusedChannelsImage, compositeTuner)

    return imagePlusComposite


#----------------SAVE FUNCTION----------------

def saveFileImage(imagePlus, imagePlusFilePath, dumpSaveFilePath, dumpFileName, separator):

    print("PATH: "+str(imagePlusFilePath))
    print("SAVE_PATH: "+str(dumpSaveFilePath))
    if os.path.isdir(dumpSaveFilePath) == False:
        os.mkdir(dumpSaveFilePath)
    fileSaver = FileSaver(imagePlus)
    imageName = imagePlus.getTitle()
    #File.makeDirectory(dumpDirectory)
    dumpFileString = str(dumpSaveFilePath)+str(separator)+str(dumpFileName)
    #filestring=File.openAsString(dumpFileString);
    #dumpFileString = str(dumpDirectory)
    #fileSaver.saveAsTiff(dumpFileString)
    #IJ.saveAsTiff(imagePlus,dumpFileString)
    IJ.saveAs(imagePlus, "Tiff", dumpFileString);



#############################################################
#----------------FOR STATIC INTERFACE WINDOW----------------#
#############################################################

#---Première fenêtre: sélection répertoire, confirmation métamorphisme et sélection du type d'opération souhaité
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

    #Select Operation Type
    choixOperation = ["Make Composite", "Make Montage"]
    selectionOperation = choixOperation[0]
    mainDialogBox.addChoice("Select Operation type you want to do",choixOperation,selectionOperation)
    mainDialogBox.addMessage("------------------------------------------")

    #Add CLIJ2 support
    booleanCLIJ = False
    mainDialogBox.addCheckbox("Utiliser CLIJ2 pour augmenter la vitesse",booleanMetamorph)
    #mainDialogBox.addMessage("On entend par fichier metamorphique un fichier de meta donnees accompagne de plusieurs fichiers image")
    mainDialogBox.addMessage("------------------------------------------")


    #Affichage de la boîte de dialogue
    mainDialogBox.showDialog();

    #Récupération choix
    folder = mainDialogBox.getNextString()
    vecteurChoix=mainDialogBox.getChoices()
    vecteurCheckBoxes=mainDialogBox.getCheckboxes()
    selectionBooleanMetamorphFiles = vecteurCheckBoxes[0]
    valeurSelectionBooleanMetamorphFiles = selectionBooleanMetamorphFiles.getState()
    selectionBooleanCLIJ = vecteurCheckBoxes[1]
    valeurSelectionBooleanCLIJ = selectionBooleanCLIJ.getState()
    selectionOperation = vecteurChoix[0]
    valeurChoixOperation = str(selectionOperation.getSelectedItem())

    if valeurSelectionBooleanCLIJ == True:
        #https://clij.github.io/clij2-docs/api_intro
        from net.haesleinhuepf.clij2 import CLIJ2;
        clij2_instance = CLIJ2.getInstance();
    if valeurSelectionBooleanCLIJ == False:
        clij2_instance = None

    #print(folder)
    if mainDialogBox.wasCanceled() == True:
        print("Cancel, End of Script")
        return None

    return folder, valeurSelectionBooleanMetamorphFiles, valeurChoixOperation, valeurSelectionBooleanCLIJ, clij2_instance

#---Deuxième fenêtre: Principale - Palette de réglages
def openDialogBoxImageTuning(selectedPath, metamorphBoolean, selectedOperation, valeurSelectionBooleanCLIJ, clij2_instance, separator):
    imageSelector = ViewedImageSelector(selectedPath, metamorphBoolean, selectedOperation, valeurSelectionBooleanCLIJ, clij2_instance, separator)

    #Instancier fenêtre de base
    imageTuningDialogBox = JFrame("Modifications d'image",
        defaultCloseOperation = JFrame.DISPOSE_ON_CLOSE, #EXIT_ON_CLOSE: ferme ImageJ en plus
        size = (1500, 500)
    )

    imageTuningDialogBoxTabs = InterfaceInstance(imageSelector, imageTuningDialogBox)
    imageTuningDialogBoxTabs.initializeBoxMultiTabContent()

    #Affichage de la boîte de dialogue
    imageTuningDialogBox.visible = True


###MAIN###
# If a Jython script is run, the variable __name__ contains the string '__main__'.
# If a script is loaded as module, __name__ has a different value.
#if __name__ in ['__builtin__','__main__']:
IJ.log('\\Clear') #efface le contenu de la console
your_os = System.getProperty("os.name");
print("Jython_plugins_path: "+str(path)) #https://imagej.net/Jython_Scripting.html#Self_written_Jython_modules_for_ImageJ
print("Java version: "+str(IJ.javaVersion()))
print("OS utilisé: "+str(your_os))
if IJ.isWindows() == True:
    separator = "\\"
elif IJ.isLinux() == True or IJ.isMacintosh() == True or IJ.isMacOSX() == True:
    separator = "/"
else:
    separator = "/"
folder, valeurSelectionBooleanMetamorphFiles, valeurChoixOperation, valeurSelectionBooleanCLIJ, clij2_instance = openMainDialogBox()
openDialogBoxImageTuning(folder, valeurSelectionBooleanMetamorphFiles, valeurChoixOperation, valeurSelectionBooleanCLIJ, clij2_instance, separator)
