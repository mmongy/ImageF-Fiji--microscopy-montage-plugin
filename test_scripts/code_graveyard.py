def convertFloatToFalse16bitShort(channelImageProcessor, booleanDoScaling):
    """
    Images de microscopie stockent 12 bits sur 16 bits.
    Recréer un ImageProcessor 16bit à partir d'un FloatProcessor est problématique à cause de ça.

    Fonction originale en Java (objet: TypeConverter):

	/** Converts a FloatProcessor to a ShortProcessor. */
	ShortProcessor convertFloatToShort() {
		float[] pixels32 = (float[])ip.getPixels();
		short[] pixels16 = new short[width*height];
		double min = ip.getMin();
		double max = ip.getMax();
		double scale;
		if ((max-min)==0.0)
			scale = 1.0;
		else
			scale = 65535.0/(max-min);
		double value;
		for (int i=0,j=0; i<width*height; i++) {
			if (doScaling)
				value = (pixels32[i]-min)*scale;
			else
				value = pixels32[i];
			if (value<0.0) value = 0.0;
			if (value>65535.0) value = 65535.0;
			pixels16[i] = (short)(value+0.5);
		}
	    return new ShortProcessor(width, height, pixels16, ip.getColorModel());
	}

    """
    imagePixels32bits = channelImageProcessor.getPixels()
    newPseudo16bitsTable = []

    imageWidth = channelImageProcessor.getWidth(); #Largeur de l'image
    imageHeight = channelImageProcessor.getHeight(); #Hauteur de l'image
    minPixelValue = channelImageProcessor.getMin();
    maxPixelValue = channelImageProcessor.getMax();

    if (maxPixelValue-minPixelValue)==0.0:
        scale = 1.0;
    else:
        scale = 4095.0/(maxPixelValue-minPixelValue)
    for pixelNumber in range(imageWidth*imageHeight):
        if booleanDoScaling == True:
            pixelValue = int((imagePixels32bits[pixelNumber]-minPixelValue)*scale)#-4096 #>> 4#2048
        else:
            pixelValue = int(imagePixels32bits[pixelNumber])#-4096 #>> 4#2048 remplacer - par +?
        if pixelValue < -4096: #0 -2048 -4096
            pixelValue = -4096 #0
        if pixelValue > 4095: #2047 4095
            pixelValue = 4095 #4095
        newPseudo16bitsTable.append(pixelValue)

    print(newPseudo16bitsTable)
    newPseudo16bitsJArray = array.array('h', newPseudo16bitsTable)
    #https://forum.image.sc/t/jython-shortprocessor-un-signed-issue/7036/3 Essayer de swapper les byts. Modifier aussi le réglage de bytes des couleurs.
    #https://docs.python.org/2/library/array.html
    #newPseudo16bitsJArray = newPseudo16bitsJArray.byteswap()
    #https://stackoverflow.com/questions/3123371/splitting-a-16-bit-int-into-two-8-bit-ints-in-python
    #https://forums.ni.com/t5/LabVIEW/Binary-Conversion-16bit-to-8bit/td-p/3195207?profile.language=en
    newPseudo16bitsShortProcessor = ShortProcessor(imageWidth, imageHeight, newPseudo16bitsJArray, channelImageProcessor.getColorModel())
    return newPseudo16bitsShortProcessor #Deprecated, test only

################################################################################

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

#############################################################################################################

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


#--------------Prototype de commande pour sauvegarde

    # ok = False
    # if (imagePlus.getStackSize() > 1):
    #      ok = fileSaver.saveAsTiffStack(imagePlus.getTitle());
    # else:
    #      ok = fileSaver.saveAsTiff(imagePlus.getTitle());
    #  	#The following call throws a NoSuchMethodError.
    #  	#ok = IJ.saveAsTiff(imp, settings.imageFilename);
    # if (ok==False):
    #      IJ.log("Failed to save image to file: " + imagePlus.getTitle());


####----------------CLIJ2


def returnBufferedCalculatedMatrixFromImagePlus(imagePlus): #unused
    #zDepthForChannel = imagePlus.getNSlices() #Profondeur Z
    imageWidth = imagePlus.getWidth(); #Largeur de l'image
    imageHeight = imagePlus.getHeight(); #Hauteur de l'image
    imageBuffer = clij2_instance.push(imagePlus)
    newBufferedImageMatrix = clij2_instance.create(Long(imageHeight, imageWidth, 1)) #, NativeTypeEnum.Float
    pass

"""
Extrait ImageJ


    /** Returns the bit depth, 8, 16, 24 (RGB) or 32. RGB images actually use 32 bits per pixel. */
    public int getBitDepth() {
        Object pixels = getPixels();
        if (pixels==null)
            return 0;
        else if (pixels instanceof byte[])
            return 8;
        else if (pixels instanceof short[])
            return 16;
        else if (pixels instanceof int[])
            return 24;
        else if (pixels instanceof float[])
            return 32;
        else
            return 0;
"""
def makeColorAdjustedChannels_CLIJ2(listOfImages, channelTuners, clij2_instance):
    coloured24bitImages = []
    for channelNumber in range(0, len(listOfImages)):
        #Conversion 32bit to 8bit
        channelImage32bit = listOfImages[channelNumber]
        channelImage32bitMatrixBuffer = clij2_instance.push(channelImage32bit)
        print("channelImage32bitMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage32bitMatrixBuffer)))
        eightBitEmptyChannelImage = IJ.createImage(channelImage32bit.getTitle(), channelImage32bit.getWidth(), channelImage32bit.getHeight(), channelImage32bit.getNSlices(), 8)
        channelImage8bitUnsignedMatrixBuffer = clij2_instance.push(eightBitEmptyChannelImage)
        print("channelImage8bitUnsignedMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage8bitUnsignedMatrixBuffer)))
        clij2_instance.multiplyImageAndScalar(channelImage32bitMatrixBuffer, channelImage8bitUnsignedMatrixBuffer, 1)
        channelImage32bitMatrixBuffer.close()

        #Calculate pixel value formula according to bit depth
        channelImageBitDepth = eightBitEmptyChannelImage.getBitDepth()
        maxImagePixelValue = (2**channelImageBitDepth)-1
        channelColor = channelTuners[channelNumber].getSelectedPseudoColor()
        channelColorRedComponent = channelColor.getRed()
        redCoefficient = float(channelColorRedComponent/maxImagePixelValue)
        channelColorGreenComponent = channelColor.getGreen()
        greenCoefficient = float(channelColorGreenComponent/maxImagePixelValue)
        channelColorBlueComponent = channelColor.getBlue()
        blueCoefficient = float(channelColorBlueComponent/maxImagePixelValue)
        totalCoefficient = float(blueCoefficient+greenCoefficient*(2**8)+redCoefficient*(2**16))

        #Calculate 24 bit pixels from 8 bit buffer and pixel value formula
        matrixBuffer24Bit = clij2_instance.create(channelImage32bit.getWidth(), channelImage32bit.getHeight(), channelImage32bit.getNSlices())
        print("matrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(matrixBuffer24Bit)))
        clij2_instance.multiplyImageAndScalar(channelImage8bitUnsignedMatrixBuffer, matrixBuffer24Bit, totalCoefficient)
        channelImage8bitUnsignedMatrixBuffer.close()

        """
        reshapedMatrixBuffer24Bit = clij2_instance.create(channelImage32bit.getWidth()*channelImage32bit.getHeight()*channelImage32bit.getNSlices(), 1, 1)
        #reshapedMatrixBuffer24Bit = clij2_instance.create(1, channelImage32bit.getWidth()*channelImage32bit.getHeight()*channelImage32bit.getNSlices(), 1)
        #reshapedMatrixBuffer24Bit = clij2_instance.create(1, 1, channelImage32bit.getWidth()*channelImage32bit.getHeight()*channelImage32bit.getNSlices())
        print("reshapedMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(reshapedMatrixBuffer24Bit)))
        matrixBuffer24Bit.copyTo(reshapedMatrixBuffer24Bit, True)
        matrixBuffer24Bit.close()
        colouredChannelMatrix = clij2_instance.pullMatXYZ(reshapedMatrixBuffer24Bit)
        reshapedMatrixBuffer24Bit.close()
        colouredChannelMatrixIntegerList = []
        for number in range(len(colouredChannelMatrix)):
            colouredChannelMatrixIntegerList.append(int(colouredChannelMatrix[number]))
        javaReshaped1DimensionColouredChannelMatrix = array.array('i', colouredChannelMatrixIntegerList)

        #gives: Exception in thread "AWT-EventQueue-0" java.awt.image.RasterFormatException: Incorrect scanline stride: 1080

        """
        colouredChannelMatrix = clij2_instance.pullMatXYZ(matrixBuffer24Bit)
        matrixBuffer24Bit.close()

        #Create images - not optimized at all - i would like to make it without loops
        channelImageRGBstack = ImageStack(channelImage32bit.getWidth(), channelImage32bit.getHeight())#, channelImage32bit.getNSlices()
        for zNumber in range(0, channelImage32bit.getNSlices()):
            sliceMatrix = []
            sliceImage = IJ.createImage("RGB Channel "+str(channelNumber)+" slice"+str(zNumber), "RGB Black", channelImage32bit.getWidth(), channelImage32bit.getHeight(), 1)
            sliceProcessor = sliceImage.getProcessor()
            for xNumber in range(len(colouredChannelMatrix)):
                for yNumber in range(len(colouredChannelMatrix[xNumber])):
                    sliceMatrix.append(int(colouredChannelMatrix[xNumber][yNumber][zNumber]))
            javaSliceMatrix = array.array('i', sliceMatrix)
            sliceProcessor.setPixels(javaSliceMatrix)
            channelImageRGBstack.addSlice(sliceProcessor)

        colouredChannelImage = ImagePlus("RGB Channel "+str(channelNumber), channelImageRGBstack)
        #colouredChannelImage.show()
        coloured24bitImages.append(colouredChannelImage)

    return coloured24bitImages

    """
    def makeFusedChannels_CLIJ2(listOfImages, clij2_instance):
        sumOfImagesBuffer = clij2_instance.push(listOfImages[0])
        for imageNumber in (1, len(listOfImages)):
            imageBuffer = clij2_instance.push(listOfImages[imageNumber])
            clij2_instance.addImages(sumOfImagesBuffer, imageBuffer, sumOfImagesBuffer)
            imageBuffer.close()
        resultImagePlus = sumOfImagesBuffer.pull()
        sumOfImagesBuffer.close()
        return resultImagePlus

    def makeFusedChannels_CLIJ2(listOfImages, clij2_instance):
        for imageNumber in (0, len(listOfImages), 2):
            image1Buffer = clij2_instance.push(listOfImages[imageNumber]) #listOfImages[0]
            image2Buffer = clij2_instance.push(listOfImages[imageNumber+1]) #listOfImages[1]
    """

def make_24bit_RGB_Channel_CLIJ2(channelImage32bit, channelNumber, selectedPseudoColor, channelImageTitle, clij2_framework):
    from net.haesleinhuepf.clij.coremem.enums import NativeTypeEnum
    clij2_instance = clij2_framework.getInstance()

    #Calculate pixel value formula according to bit depth
    channelImageBitDepth = 8
    maxImagePixelValue = (2**channelImageBitDepth)-1
    channelColorRedComponent = selectedPseudoColor.getRed()
    redCoefficient = float(channelColorRedComponent/maxImagePixelValue)
    channelColorGreenComponent = selectedPseudoColor.getGreen()
    greenCoefficient = float(channelColorGreenComponent/maxImagePixelValue)
    channelColorBlueComponent = selectedPseudoColor.getBlue()
    blueCoefficient = float(channelColorBlueComponent/maxImagePixelValue)
    totalCoefficient = float(blueCoefficient+greenCoefficient*(2**8)+redCoefficient*(2**16))


    channelImageRGBstack = ImageStack(channelImage32bit.getWidth(), channelImage32bit.getHeight())
    """
    #Extract stack from image and work slice by slice -> bad idea, give weird images
    channelImage32bitStack = channelImage32bit.getStack()
    for zDepthNumber in range(1, channelImage32bit.getNSlices()+1):
        channelImageSliceProcessor32bit = channelImage32bitStack.getProcessor(zDepthNumber)
        channelImageSlice32bitMatrix = channelImageSliceProcessor32bit.getPixels()
        print("channelImageSlice32bitMatrix: "+str(channelImageSlice32bitMatrix))
        channelImageSlice32bitMatrixBuffer = clij2_instance.pushMatXYZ(channelImageSlice32bitMatrix)
        #channelImageSlice32bitMatrixBuffer = clij2_instance.pushMat(channelImageSlice32bitMatrix) #Exception in thread "AWT-EventQueue-0" java.lang.IllegalArgumentException: Conversion of [S@5e5d2eb / [S not supported -> shorts
        print("channelImageSlice32bitMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImageSlice32bitMatrixBuffer))+", "+str(channelImageSlice32bitMatrixBuffer.getDimension()))
        channelImage8bitUnsignedSliceMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedByte); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
        print("channelImage8bitUnsignedSliceMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage8bitUnsignedSliceMatrixBuffer))+", "+str(channelImage8bitUnsignedSliceMatrixBuffer.getDimension()))
        clij2_instance.copy(channelImageSlice32bitMatrixBuffer, channelImage8bitUnsignedSliceMatrixBuffer);

        #Calculate 24 bit pixels from 8 bit buffer and pixel value formula
        sliceMatrixBuffer24Bit = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedInt) #Conversion floats to integers
        print("sliceMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(sliceMatrixBuffer24Bit))+", "+str(sliceMatrixBuffer24Bit.getDimension()))
        clij2_instance.multiplyImageAndScalar(channelImage8bitUnsignedSliceMatrixBuffer, sliceMatrixBuffer24Bit, totalCoefficient)
        colouredChannelMatrix = clij2_instance.pullMatXYZ(sliceMatrixBuffer24Bit)
        print("colouredChannelMatrix: "+str(colouredChannelMatrix))

        sliceMatrix = []
        javaSliceMatrix = array.array('i', sliceMatrix)
        sliceImage = IJ.createImage("RGB Channel "+str(channelNumber)+" slice"+str(zDepthNumber), "RGB Black", channelImage32bit.getWidth(), channelImage32bit.getHeight(), 1)
        sliceProcessor = sliceImage.getProcessor()
        for xNumber in range(len(colouredChannelMatrix)):
            javaSliceMatrix = javaSliceMatrix+colouredChannelMatrix[xNumber]
        sliceProcessor.setPixels(javaSliceMatrix)
        channelImageRGBstack.addSlice(sliceProcessor)

        channelImage8bitUnsignedSliceMatrixBuffer.close()
        channelImageSlice32bitMatrixBuffer.close()

        #Transpose matrix24bit
        #transposedMatrixBuffer24Bit = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedInt)
        #print("transposedMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(transposedMatrixBuffer24Bit))+", "+str(transposedMatrixBuffer24Bit.getDimension()))
        #clij2_instance.transposeYZ(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)
        #clij2_instance.transposeXZ(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)
        #clij2_instance.transposeXY(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)

        #Reshape slice matrix
        reshapedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth()*channelImage32bit.getHeight(), 1], NativeTypeEnum.UnsignedInt)
        print("reshapedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
        sliceMatrixBuffer24Bit.copyTo(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer, True)

        #Extract matrix from buffer
        reshapedSliceContainer = clij2_instance.pullMat(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
        #reshapedSliceContainer = clij2_instance.pullMatXYZ(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
        print("reshapedSliceContainer: "+str(reshapedSliceContainer))

        #Set pixels to image
        imagePluses = []
        for sliceMatrix in reshapedSliceContainer:
            print("sliceMatrix: "+str(sliceMatrix))
            sliceImage = IJ.createImage("RGB Channel "+str(channelNumber)+" slice"+str(zDepthNumber), "RGB Black", channelImage32bit.getWidth(), channelImage32bit.getHeight(), 1)
            sliceProcessor = sliceImage.getProcessor()
            sliceProcessor.setPixels(sliceMatrix)
            sliceImage.setProcessor(sliceProcessor)
            imagePluses.append(sliceImage)
        print("imagePluses: "+str(imagePluses))
        realColouredChannelImage = imagePluses[0]
        realColouredChannelImageProcessor = realColouredChannelImage.getProcessor()
        channelImageRGBstack.addSlice(realColouredChannelImageProcessor)

        #Close every buffer
        reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
        sliceMatrixBuffer24Bit.close()
        #transposedMatrixBuffer24Bit.close()
        channelImage8bitUnsignedSliceMatrixBuffer.close()
        channelImageSlice32bitMatrixBuffer.close()

    """

    """
    #Conversion 32bit to 8bit
    channelImageProcessor32bit = channelImage32bit.getProcessor()
    channelImage32bitMatrix = channelImageProcessor32bit.getPixels()
    #print("channelImage32bitMatrix: "+str(channelImage32bitMatrix))
    #channelImage32bitMatrixBuffer = clij2_instance.pushMatXYZ(channelImage32bitMatrix)
    #channelImage32bitMatrixBuffer = clij2_instance.pushMat(channelImage32bitMatrix) #Exception in thread "AWT-EventQueue-0" java.lang.IllegalArgumentException: Conversion of [S@5e5d2eb / [S not supported -> shorts
    channelImage32bitMatrixBuffer = clij2_instance.push(channelImage32bit) #Permet d'importer l'image entière en 3D contrairement à pushMat et pusMatXYZ. Peut-être lié à getPixels(). Convertir en stack puis faire par slice?
    print("channelImage32bitMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage32bitMatrixBuffer))+", "+str(channelImage32bitMatrixBuffer.getDimension()))
    channelImage8bitUnsignedMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight(), channelImage32bit.getNSlices()], NativeTypeEnum.UnsignedByte); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
    print("channelImage8bitUnsignedMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage8bitUnsignedMatrixBuffer))+", "+str(channelImage8bitUnsignedMatrixBuffer.getDimension()))
    clij2_instance.copy(channelImage32bitMatrixBuffer, channelImage8bitUnsignedMatrixBuffer);

    #Calculate 24 bit pixels from 8 bit buffer and pixel value formula
    matrixBuffer24Bit = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight(), channelImage32bit.getNSlices()], NativeTypeEnum.UnsignedInt) #Conversion floats to integers
    print("matrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(matrixBuffer24Bit))+", "+str(matrixBuffer24Bit.getDimension()))
    clij2_instance.multiplyImageAndScalar(channelImage8bitUnsignedMatrixBuffer, matrixBuffer24Bit, totalCoefficient)
    #colouredChannelMatrix = clij2_instance.pullMatXYZ(matrixBuffer24Bit)
    #print("colouredChannelMatrix: "+str(colouredChannelMatrix))



    #Create images - No GPU part - not optimized at all - i would like to make it without loops
    #Reshape matrix and extract each Z-Depth with for loop
    channelImageRGBstack = ImageStack(channelImage32bit.getWidth(), channelImage32bit.getHeight())
    colouredChannelMatrix = clij2_instance.pullMatXYZ(matrixBuffer24Bit)
    for zNumber in range(0, channelImage32bit.getNSlices()):
        sliceMatrix = []
        sliceImage = IJ.createImage("RGB Channel "+str(channelNumber)+" slice"+str(zNumber), "RGB Black", channelImage32bit.getWidth(), channelImage32bit.getHeight(), 1)
        sliceProcessor = sliceImage.getProcessor()
        for xNumber in range(len(colouredChannelMatrix)):
            for yNumber in range(len(colouredChannelMatrix[xNumber])):
                sliceMatrix.append(int(colouredChannelMatrix[xNumber][yNumber][zNumber]))
        javaSliceMatrix = array.array('i', sliceMatrix)
        sliceProcessor.setPixels(javaSliceMatrix)
        channelImageRGBstack.addSlice(sliceProcessor)
    """


    """
    #Transpose matrix24bit
    #transposedMatrixBuffer24Bit = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getNSlices(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedInt)
    transposedMatrixBuffer24Bit = clij2_instance.create([channelImage32bit.getNSlices(), channelImage32bit.getHeight(), channelImage32bit.getWidth()], NativeTypeEnum.UnsignedInt)
    print("transposedMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(transposedMatrixBuffer24Bit))+", "+str(transposedMatrixBuffer24Bit.getDimension()))
    #clij2_instance.transposeYZ(matrixBuffer24Bit, transposedMatrixBuffer24Bit)
    clij2_instance.transposeXZ(matrixBuffer24Bit, transposedMatrixBuffer24Bit)
    #clij2_instance.transposeXY(matrixBuffer24Bit, transposedMatrixBuffer24Bit)

    #Reshape matrix and extract each Z-Depth
    channelImageRGBstack = ImageStack(channelImage32bit.getWidth(), channelImage32bit.getHeight())
    #channelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth()*channelImage32bit.getHeight(), 1], NativeTypeEnum.UnsignedInt)
    channelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedInt)
    print("channelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(channelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
    XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth(), channelImage32bit.getHeight()], NativeTypeEnum.UnsignedInt)
    print("XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
    reshapedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([channelImage32bit.getWidth()*channelImage32bit.getHeight(), 1], NativeTypeEnum.UnsignedInt)
    print("reshapedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
    for zNumber in range(0, channelImage32bit.getNSlices()):
        #clij2_instance.copySlice(matrixBuffer24Bit, channelImageSliceUnsignedIntegerMatrixBuffer, zNumber) #RuntimeError: maximum recursion depth exceeded (Java StackOverflowError)
        clij2_instance.copySlice(transposedMatrixBuffer24Bit, channelImageSliceUnsignedIntegerMatrixBuffer, zNumber)
        #sliceContainer = clij2_instance.pullMat(channelImageSliceUnsignedIntegerMatrixBuffer)
        sliceContainer = clij2_instance.pullMatXYZ(channelImageSliceUnsignedIntegerMatrixBuffer)
        print("sliceContainer: "+str(sliceContainer))

        clij2_instance.transposeXY(channelImageSliceUnsignedIntegerMatrixBuffer, XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer)
        XYtransposedChannelImageSliceContainer = clij2_instance.pullMatXYZ(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer)
        print("XYtransposedChannelImageSliceContainer: "+str(XYtransposedChannelImageSliceContainer))

        clij2_instance.copy(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer, reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
        reshapedSliceContainer = clij2_instance.pullMat(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
        #reshapedSliceContainer = clij2_instance.pullMatXYZ(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
        print("reshapedSliceContainer: "+str(reshapedSliceContainer))
        imagePluses = []
        #Set pixels to image
        for sliceMatrix in reshapedSliceContainer:
            print("sliceMatrix: "+str(sliceMatrix))
            sliceImage = IJ.createImage("RGB Channel "+str(channelNumber)+" slice"+str(zNumber), "RGB Black", channelImage32bit.getWidth(), channelImage32bit.getHeight(), 1)
            sliceProcessor = sliceImage.getProcessor()
            sliceProcessor.setPixels(sliceMatrix)
            sliceImage.setProcessor(sliceProcessor)
            imagePluses.append(sliceImage)
        print("imagePluses: "+str(imagePluses))
        realColouredChannelImage = imagePluses[0]
        #realColouredChannelImage.show()
        realColouredChannelImageProcessor = realColouredChannelImage.getProcessor()
        channelImageRGBstack.addSlice(realColouredChannelImageProcessor)


    #Close every buffer
    reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
    XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
    channelImageSliceUnsignedIntegerMatrixBuffer.close()
    transposedMatrixBuffer24Bit.close()
    channelImage32bitMatrixBuffer.close()
    channelImage8bitUnsignedMatrixBuffer.close()
    matrixBuffer24Bit.close()
    """

    #Convert stack to ImagePlus
    colouredChannelImage = ImagePlus(String(channelImageTitle), channelImageRGBstack)

    return colouredChannelImage


def makeMontage_24bit_from_Matrixes(stackImp, numberOfColumns, numberOfRows): #Testing only - No difference in term of time with the original function.

    def divide_chunks(l, n):
        """
        Provient de: https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
        """
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    #clij2_instance = clij2_framework.getInstance()
    bitDepth = stackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    imageWidth = stackImp.getWidth(); #Largeur de l'image
    imageHeight = stackImp.getHeight(); #Hauteur de l'image
    numberOfSlices = stackImp.getNSlices() #Nombre d'images du stack
    montageWidth = imageWidth*int(numberOfColumns)
    montageHeight = imageHeight*int(numberOfRows)
    stackedImages = stackImp.getStack()
    totalNumberOfImages = stackedImages.getSize() #Profondeur Z * Nombre de canaux

    arrayOfImages = separateByChannels(stackImp)
    #print("length arrayOfImages: "+str(len(arrayOfImages)))
    #print("arrayOfImages: "+str(arrayOfImages))

    montageTimeStack = ImageStack(montageWidth, montageHeight)
    sliceMatrixes = []
    for zDepthImageTimeArray in arrayOfImages:
        zDepthImagePlus = zDepthImageTimeArray[0]
        zDepthImageStack = zDepthImagePlus.getStack()
        numberOfChannelsOfStack = zDepthImageStack.getSize()
        for channelNumber in range(1, numberOfChannelsOfStack+1):
            sliceChannelProcessor = zDepthImageStack.getProcessor(channelNumber)
            sliceChannelMatrix = sliceChannelProcessor.getPixelsCopy()
            sliceMatrixes.append(sliceChannelMatrix)

    #reshapedMatrix = list(divide_chunks(sliceMatrixes, numberOfSlices))
    #print("pythonReshapedImageMatrix: "+str(reshapedMatrix))

    def stickMatrixes(arrayOfChannelMatrixes, imageHeight, imageWidth):
        """
        print("arrayOfChannelMatrixes: "+str(arrayOfChannelMatrixes))
        montageMatrix = []
        for height in range(0, imageHeight):
            heightPosition = imageWidth*height
            for channelNumber in range(0, len(arrayOfChannelMatrixes)):
                for pixelNumber in range(0, imageWidth):
                    pixelValue = arrayOfChannelMatrixes[channelNumber][heightPosition+pixelNumber]
                    montageMatrix.append(pixelValue)
        javaMontageImageMatrix = array.array('i', montageMatrix)
        """
        javaMontageImageMatrix = array.array('i', [0]*(montageWidth*montageHeight)) #https://stackoverflow.com/questions/10712002/create-an-empty-list-in-python-with-certain-size
        imageNumber = 0
        montageOrigin = 0
        for imageMatrix in arrayOfChannelMatrixes:
            imageOrigin = 0
            increment = 0
            for loopTurn in range(0, montageHeight):
                javaImageMatrix = array.array('i', imageMatrix)
                System.arraycopy(javaImageMatrix, imageOrigin, javaMontageImageMatrix, montageOrigin+increment, imageWidth); #https://www.tutorialspoint.com/java/lang/system_arraycopy.htm
                imageNumber+=1
                imageOrigin+=imageWidth
                increment+=montageWidth
            montageOrigin+=imageWidth
        return javaMontageImageMatrix

    newMontageImageRGBstack = ImageStack(montageWidth, montageHeight)
    zDepth = 1
    #for zDepthArray in reshapedMatrix:
    newMontageSliceImagePlus = IJ.createImage("Montage slice "+str(zDepth), "RGB Black", montageWidth, montageHeight, 1)
    newMontageSliceImageProcessor = newMontageSliceImagePlus.getProcessor()
    #javaMontageImageMatrix = stickMatrixes(zDepthArray, imageHeight, imageWidth)
    javaMontageImageMatrix = stickMatrixes(sliceMatrixes, imageHeight, imageWidth)
    newMontageSliceImageProcessor.setPixels(javaMontageImageMatrix)
    newMontageImageRGBstack.addSlice(newMontageSliceImageProcessor)
    zDepth+=1

    newMontageImagePlus = ImagePlus(String("Montage"), newMontageImageRGBstack)
    return newMontageImagePlus, montageWidth, montageHeight

def makeMontage_24bit_CLIJ2(stackImp, numberOfColumns, numberOfRows, clij2_framework):
    from net.haesleinhuepf.clij.coremem.enums import NativeTypeEnum

    def divide_chunks(l, n):
        """
        Provient de: https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
        """
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    #https://clij.github.io/clij2-docs/md/crop_and_paste/
    clij2_instance = clij2_framework.getInstance()
    bitDepth = stackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    imageWidth = stackImp.getWidth(); #Largeur de l'image
    imageHeight = stackImp.getHeight(); #Hauteur de l'image
    numberOfSlices = stackImp.getNSlices() #Nombre d'images du stack

    numberOfChannels = stackImp.getNChannels() #Nombre de canaux
    print("numberOfChannels: "+str(numberOfChannels))
    zDepthByChannel = stackImp.getNSlices() #Profondeur Z
    print("zDepthByChannel: "+str(zDepthByChannel))
    vignettesImageStack = stackImp.getStack()
    totalSize = vignettesImageStack.getSize()
    print("totalSize: "+str(totalSize))

    montageWidth = imageWidth*int(numberOfColumns)
    montageHeight = imageHeight*int(numberOfRows)

    arrayOfImages = separateByChannels(stackImp)
    #print("length arrayOfImages: "+str(len(arrayOfImages)))
    #print("arrayOfImages: "+str(arrayOfImages))

    montageTimeStack = ImageStack(montageWidth, montageHeight)
    sliceMatrixes = []
    for zDepthImageTimeArray in arrayOfImages:
        zDepthImagePlus = zDepthImageTimeArray[0]
        zDepthImageStack = zDepthImagePlus.getStack()
        numberOfChannelsOfStack = zDepthImageStack.getSize()
        for channelNumber in range(1, numberOfChannelsOfStack+1):
            sliceChannelProcessor = zDepthImageStack.getProcessor(channelNumber)
            sliceChannelMatrix = sliceChannelProcessor.getPixelsCopy()
            sliceMatrixes.append(sliceChannelMatrix)

    #reshapedMatrix = list(divide_chunks(sliceMatrixes, numberOfSlices))
    #print("pythonReshapedImageMatrix: "+str(reshapedMatrix))

    def stickMatrixes(arrayOfChannelMatrixes, montageHeight, montageWidth, imageHeight, imageWidth):
        """
        montageMatrix = array.array('i', [0]*(montageWidth*montageHeight)) #https://stackoverflow.com/questions/10712002/create-an-empty-list-in-python-with-certain-size
        imageNumber = 0
        montageOrigin = 0
        for imageMatrix in arrayOfChannelMatrixes:
            imageOrigin = 0
            increment = 0
            for loopTurn in range(0, montageHeight):
                javaImageMatrix = array.array('i', imageMatrix)
                System.arraycopy(javaImageMatrix, imageOrigin, montageMatrix, montageOrigin+increment, imageWidth); #https://www.tutorialspoint.com/java/lang/system_arraycopy.htm
                imageNumber+=1
                imageOrigin+=imageWidth
                increment+=montageWidth
            montageOrigin+=imageWidth
        montageMatrixBuffer = clij2_instance.pushMat(montageMatrix)

        """
        montageMatrixBuffer = clij2_instance.create([montageWidth, montageHeight], NativeTypeEnum.UnsignedInt)
        yOrigin = 0
        xOrigin = 0
        for imageMatrix in arrayOfChannelMatrixes:
            print("imageMatrix: "+str(imageMatrix))
            imageMatrixBuffer = clij2_instance.pushMat(imageMatrix)
            for yValue in range(imageWidth):
                for xValue in range(imageHeight):
                    clij2_instance.paste(imageMatrixBuffer, montageMatrixBuffer, xOrigin+xValue, yOrigin+yValue)
            #clij2_instance.paste(imageMatrixBuffer, montageMatrixBuffer, xOrigin, yOrigin)
            imageMatrixBuffer.close()
            xOrigin = xOrigin+imageWidth
            if xOrigin >= montageWidth:
                xOrigin = 0
                yOrigin = yOrigin+imageHeight


        reshapedMontageMatrixBuffer = clij2_instance.create([montageWidth*montageHeight, 1], NativeTypeEnum.UnsignedInt)
        montageMatrixBuffer.copyTo(reshapedMontageMatrixBuffer, True)
        montageContainer = clij2_instance.pullMat(reshapedMontageMatrixBuffer)
        montageMatrix = montageContainer[0]
        montageMatrixBuffer.close()
        reshapedMontageMatrixBuffer.close()

        return montageMatrix


    newMontageImageRGBstack = ImageStack(montageWidth, montageHeight)
    zDepth = 1
    #for zDepthArray in arrayOfImages: #reshapedMatrix:
    newMontageSliceImagePlus = IJ.createImage("Montage slice "+str(zDepth), "RGB Black", montageWidth, montageHeight, 1)
    newMontageSliceImageProcessor = newMontageSliceImagePlus.getProcessor()
    #javaMontageImageMatrix = stickMatrixes(zDepthArray, montageHeight, montageWidth)
    javaMontageImageMatrix = stickMatrixes(sliceMatrixes, montageHeight, montageWidth, imageHeight, imageWidth)
    newMontageSliceImageProcessor.setPixels(javaMontageImageMatrix)
    newMontageImageRGBstack.addSlice(newMontageSliceImageProcessor)
    zDepth+=1

    newMontageImagePlus = ImagePlus(String("Montage"), newMontageImageRGBstack)
    #montageTimeStack.addSlice(newMontageImagePlus.getProcessor())
    #fullMontageImagePlus = ImagePlus(String("Montage"), montageTimeStack)
    return newMontageImagePlus, montageWidth, montageHeight


def makeMontage_CLIJ2(stackImp, numberOfColumns, numberOfRows, clij2_framework): #Partially dysfunctional because CLIJ2 doesn't work on 24bit (3x8bit) RGB images
    #https://clij.github.io/clij2-docs/md/crop_and_paste/
    clij2_instance = clij2_framework.getInstance()
    #stackImp.show()
    bitDepth = stackImp.getBitDepth() #Type de l'image en bits - Returns the bit depth, 8, 16, 24 (RGB) or 32, or 0 if the bit depth is unknown. RGB images actually use 32 bits per pixel.
    imageWidth = stackImp.getWidth(); #Largeur de l'image
    imageHeight = stackImp.getHeight(); #Hauteur de l'image
    numberOfSlices = stackImp.getNSlices() #Nombre d'images du stack
    montageWidth = imageWidth*int(numberOfColumns)
    montageHeight = imageHeight*int(numberOfRows)

    # convert ImageJ image to CL images (ready for the GPU)
    #stackImpBuffer = clij2_instance.push(stackImp);
    newMontageImageBuffer = clij2_instance.create([montageWidth, montageHeight]); # allocate memory for result image. place zdepth?

    yMontage = 0
    xMontage = 0

    #processorBuffers = []
    vignettesImageStack = stackImp.getStack()
    #arrayOfImages = separateByChannels(stackImp)
    for imageNumber in range(0, numberOfSlices): #Prend toutes les Z detous les canaux -> à corriger
        #vignetteImagePlus = arrayOfImages[imageNumber]
        vignetteImagePlus = stackImp.createImagePlus()
        vignetteImageProcessor = vignettesImageStack.getProcessor(imageNumber+1)
        vignetteImagePlus.setProcessor(vignetteImageProcessor)
        #vignetteImagePlus.show()
        vignetteImageBuffer = clij2_instance.push(vignetteImagePlus);
        clij2_instance.paste2D(vignetteImageBuffer, newMontageImageBuffer, xMontage, yMontage)
        vignetteImageBuffer.close()
        if xMontage*yMontage >= montageWidth*montageHeight:
            break
        if xMontage < montageWidth:# and newXOrigin != 0:
            xMontage = xMontage+imageWidth
            yMontage = yMontage
        if xMontage == montageWidth:
            xMontage = 0
            yMontage = yMontage+imageHeight

    # convert the result back to imglib2
    newMontageImagePlus = clij2_instance.pull(newMontageImageBuffer)

    # free memory on the GPU - needs to be done explicitly
    #stackImpBuffer.close()
    newMontageImageBuffer.close()

    return newMontageImagePlus, montageWidth, montageHeight

        #zProjectedTunedImagesCopy = copy.deepcopy(zProjectedTunedImages) #Ne fonctionne pas car objets Java non sérialisables.
        #fusedChannelsImage = makeFusedChannels_CLIJ2(zProjectedTunedImagesNeededCopy, clij2_framework) #Fonction récursive agissant directement sur le tableau pris en paramètre, d'où l'intérêt de la copie.

def makeFusedChannels_CLIJ2(listOfImages, clij2_framework):

    #Ajoute récursivement les images pour contourner la limite de 2 images des fonctions de CLIJ2.
    #Echoue à faire un composite, fait juste un merge. Peut-être pour montages en niveaux de gris...
    clij2_instance = clij2_framework.getInstance()
    if len(listOfImages) == 1:
        leveledCompositeImage = listOfImages[0]
        leveledCompositeImage.setTitle("Fused Image")
        return leveledCompositeImage
    if len(listOfImages) > 1:
        image1Buffer = clij2_instance.push(listOfImages.pop(0)) #listOfImages[0]
        image2Buffer = clij2_instance.push(listOfImages.pop(0)) #listOfImages[1]
        sumOfImagesBuffer = clij2_instance.create(image1Buffer)
        clij2_instance.addImages(image1Buffer, image2Buffer, sumOfImagesBuffer)
        resultImagePlus = clij2_instance.pull(sumOfImagesBuffer)
        sumOfImagesBuffer.close()
        image2Buffer.close()
        image1Buffer.close()
        listOfImages.append(resultImagePlus)
        return makeFusedChannels_CLIJ2(listOfImages, clij2_framework)


def separateChannelByTime(channelImagePlus, totalTime): # l'intégrer dans la fonction ci-dessus
    listOfTimeStampsImagePluses = []
    imageWidth = channelImagePlus.getWidth(); #Largeur de l'image
    imageHeight = channelImagePlus.getHeight(); #Hauteur de l'image
    channelStackedImages = channelImagePlus.getStack()
    channelTotalNumberOfImages = channelStackedImages.getSize() #Profondeur Z * Nombre de canaux * temps
    timeStack = ImageStack(imageWidth, imageHeight)
    for timeStamp in range(0, channelTotalNumberOfImages, totalTime): #channelNumber
        sliceTitle = channelStackedImages.getSliceLabel(timeStamp+1)
        sliceProcessor = channelStackedImages.getProcessor(timeStamp+1)
        channelStack.addSlice(sliceTitle, sliceProcessor)
    channelTitle = String("Channel "+str(channelNumber+1))
    channelImagePlus = ImagePlus(channelTitle, channelStack)
    arrayOfChannels.append(channelImagePlus)
    return listOfTimeStampsImagePluses



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
                #sourceSliceIndex = channelNumber + timeNumber*nFirst + zNumber*nFirst*nMiddle
                #print("destinationSliceIndex: "+str(destinationSliceIndex)+", sourceSliceIndex: "+str(channelNumber)+"+"+str(timeNumber)+"*"+str(nFirst)+"+"+str(zNumber)+"*"+str(nFirst)+"*"+str(nMiddle)+" = "+str(sourceSliceIndex))
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
    shuffledHyperStackImagePlus = HyperStackConverter.toHyperStack(shuffledHyperStackImagePlus, nFirst, nMiddle, nLast)
    return shuffledHyperStackImagePlus
