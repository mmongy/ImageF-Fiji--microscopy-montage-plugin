import os, sys
from sys import path
import time
import java, jarray, array
from java.io import File
from java.lang import System, String, Byte, Double, Float, Integer, Long, Short
from ij import IJ, ImageStack, ImagePlus, CompositeImage, ImageListener, VirtualStack, WindowManager
from ij.process import ImageProcessor, FloatProcessor, ShortProcessor, ByteProcessor, ColorProcessor, LUT
from net.haesleinhuepf.clij.clearcl import ClearCLBuffer
from net.haesleinhuepf.clij.coremem.enums import NativeTypeEnum
from net.haesleinhuepf.clij2 import CLIJ2

IJ.log('\\Clear') #efface le contenu de la console
grayLevelImagePlus = IJ.openImage()
grayLevelImagePlus.show()
totalCoefficient = float(1.5)

grayLevelImagePlusProcessor = grayLevelImagePlus.getProcessor()
grayLevelImagePlusMatrix = grayLevelImagePlusProcessor.getPixels()
#testGrayLevelImageMatrixBuffer = clij2_instance.pushMatXYZ(grayLevelImagePlusMatrix)


# init GPU
clij2_instance = CLIJ2.getInstance()

#Conversion 32bit to 8bit

testGrayLevelImageMatrixBuffer = clij2_instance.push(grayLevelImagePlus)
print("testGrayLevelImageMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(testGrayLevelImageMatrixBuffer))+", "+str(testGrayLevelImageMatrixBuffer.getDimension()))
#clij2_instance.print(testGrayLevelImageMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'
test8bitUnsignedMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(testGrayLevelImageMatrixBuffer), NativeTypeEnum.UnsignedByte); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
clij2_instance.copy(testGrayLevelImageMatrixBuffer, test8bitUnsignedMatrixBuffer);
clij2_instance.print(test8bitUnsignedMatrixBuffer)


#Trying a pixel by pixel multiplication
totalCoefficient = float(1)
testMatrixBuffer24Bit = clij2_instance.create(clij2_instance.getDimensions(testGrayLevelImageMatrixBuffer))
clij2_instance.print(testMatrixBuffer24Bit)
clij2_instance.multiplyImageAndScalar(test8bitUnsignedMatrixBuffer, testMatrixBuffer24Bit, totalCoefficient)


#Conversion floats to integers
testUnsignedIntegerMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(testGrayLevelImageMatrixBuffer), NativeTypeEnum.UnsignedInt); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
clij2_instance.copy(testMatrixBuffer24Bit, testUnsignedIntegerMatrixBuffer)
#clij2_instance.print(testUnsignedIntegerMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'

witnessMatrix = clij2_instance.pullMatXYZ(testUnsignedIntegerMatrixBuffer)
print("witnessMatrix: ", str(witnessMatrix))

#Reshape matrix
#reshapedTestIntegerMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(testGrayLevelImageMatrixBuffer), NativeTypeEnum.UnsignedInt)
#clij2_instance.copy(testUnsignedIntegerMatrixBuffer, reshapedTestIntegerMatrixBuffer)
#clij2_instance.print(reshapedTestIntegerMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'

#Create images - No GPU part - not optimized at all - i would like to make it without loops
#Reshape matrix and extract each Z-Depth with for loop

################
#1st try, build image with for loops
################

#channelImageRGBstack = ImageStack(grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight())
channelImageRGBstack_1st_try = ImageStack(grayLevelImagePlus.getHeight(), grayLevelImagePlus.getWidth())
print("testUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(testUnsignedIntegerMatrixBuffer))+", "+str(testUnsignedIntegerMatrixBuffer.getDimension()))
colouredChannelMatrix = clij2_instance.pullMatXYZ(testUnsignedIntegerMatrixBuffer)
#colouredChannelMatrix = clij2_instance.pullMat(testUnsignedIntegerMatrixBuffer)
list_of_matrixes_1st_try = []
for zNumber in range(0, grayLevelImagePlus.getNSlices()):
    sliceMatrix = []
    #sliceImage = IJ.createImage("RGB Channel "+str(0)+" slice"+str(zNumber), "RGB Black", grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight(), 1)
    sliceImage = IJ.createImage("RGB Channel "+str(0)+" slice"+str(zNumber), "RGB Black", grayLevelImagePlus.getHeight(), grayLevelImagePlus.getWidth(), 1)
    sliceProcessor = sliceImage.getProcessor()
    for xNumber in range(len(colouredChannelMatrix)):
        for yNumber in range(len(colouredChannelMatrix[xNumber])):
            sliceMatrix.append(int(colouredChannelMatrix[xNumber][yNumber][zNumber]))
    javaSliceMatrix = array.array('i', sliceMatrix)
    list_of_matrixes_1st_try.append(javaSliceMatrix)
    sliceProcessor.setPixels(javaSliceMatrix)
    channelImageRGBstack_1st_try.addSlice(sliceProcessor)

print("list_of_matrixes_1st_try: ", str(list_of_matrixes_1st_try))
#Convert stack to ImagePlus
colouredChannelImage_1st_try = ImagePlus(String("Processed image with loops"), channelImageRGBstack_1st_try)
colouredChannelImage_1st_try.show()


################
#2nd try, use CLIJ buffers to build image
################

#Reshape matrix and extract each Z-Depth
channelImageRGBstack_2nd_try = ImageStack(grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight())
#channelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth()*channelImage32bit.getHeight(), 1], NativeTypeEnum.UnsignedInt)
channelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight()], NativeTypeEnum.UnsignedInt)
print("channelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(channelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
#XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight()], NativeTypeEnum.UnsignedInt)
#print("XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
reshapedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth()*grayLevelImagePlus.getHeight(), 1], NativeTypeEnum.UnsignedInt)
print("reshapedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
list_of_matrixes_2nd_try = []
for zNumber in range(0, grayLevelImagePlus.getNSlices()):
    #clij2_instance.copySlice(matrixBuffer24Bit, channelImageSliceUnsignedIntegerMatrixBuffer, zNumber) #RuntimeError: maximum recursion depth exceeded (Java StackOverflowError)
    clij2_instance.copySlice(testMatrixBuffer24Bit, channelImageSliceUnsignedIntegerMatrixBuffer, zNumber)
    #sliceContainer = clij2_instance.pullMat(channelImageSliceUnsignedIntegerMatrixBuffer)
    sliceContainer = clij2_instance.pullMatXYZ(channelImageSliceUnsignedIntegerMatrixBuffer)
    #print("sliceContainer: "+str(sliceContainer))
    #clij2_instance.transposeXY(channelImageSliceUnsignedIntegerMatrixBuffer, XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer)
    #XYtransposedChannelImageSliceContainer = clij2_instance.pullMatXYZ(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer)
    #print("XYtransposedChannelImageSliceContainer: "+str(XYtransposedChannelImageSliceContainer))

    #clij2_instance.copy(XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer, reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    clij2_instance.copy(channelImageSliceUnsignedIntegerMatrixBuffer, reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    reshapedSliceContainer = clij2_instance.pullMat(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    #reshapedSliceContainer = clij2_instance.pullMatXYZ(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    list_of_matrixes_2nd_try.append(sliceContainer)
    #print("reshapedSliceContainer: "+str(reshapedSliceContainer))
    imagePluses = []
    #Set pixels to image
    for sliceMatrix in reshapedSliceContainer:
        #print("sliceMatrix: "+str(sliceMatrix))
        sliceImage = IJ.createImage("RGB Channel "+str(0)+" slice"+str(zNumber), "RGB Black", grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight(), 1)
        sliceProcessor = sliceImage.getProcessor()
        sliceProcessor.setPixels(sliceMatrix)
        sliceImage.setProcessor(sliceProcessor)
        imagePluses.append(sliceImage)
    print("imagePluses: "+str(imagePluses))
    realColouredChannelImage = imagePluses[0]
    #realColouredChannelImage.show()
    realColouredChannelImageProcessor = realColouredChannelImage.getProcessor()
    channelImageRGBstack_2nd_try.addSlice(realColouredChannelImageProcessor)
print("list_of_matrixes_2nd_try: ", str(list_of_matrixes_2nd_try ))
#Close buffers

reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
#XYtransposedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
channelImageSliceUnsignedIntegerMatrixBuffer.close()
testUnsignedIntegerMatrixBuffer.close()
testMatrixBuffer24Bit.close()
test8bitUnsignedMatrixBuffer.close()

#Convert stack to ImagePlus
colouredChannelImage_2nd_try = ImagePlus(String("Processed image with CLIJ buffers"), channelImageRGBstack_2nd_try)
colouredChannelImage_2nd_try.show()



################
#3rd try, use CLIJ buffers to build image, but extract stack from image and work slice by slice before creating buffers
################

channelImageRGBstack_3rd_try = ImageStack(grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight())
#Extract stack from image and work slice by slice (to exclude potential problems when trying to push the whole image with push() or when trying to use the matrix with getPixels()/pushMat() or getPixels()/pushMatXYZ() directly.)
grayLevelImagePlusStack = grayLevelImagePlus.getStack()
for zDepthNumber in range(1, grayLevelImagePlus.getNSlices()+1):
    channelImageSliceProcessor8bit = grayLevelImagePlusStack.getProcessor(zDepthNumber)
    channelImageSlice32bitMatrix = channelImageSliceProcessor8bit.getPixels()
    #print("channelImageSlice32bitMatrix: "+str(channelImageSlice32bitMatrix))
    channelImageSlice32bitMatrixBuffer = clij2_instance.pushMatXYZ(channelImageSlice32bitMatrix)
    #channelImageSlice32bitMatrixBuffer = clij2_instance.pushMat(channelImageSlice32bitMatrix) #Exception in thread "AWT-EventQueue-0" java.lang.IllegalArgumentException: Conversion of [S@5e5d2eb / [S not supported -> shorts
    #print("channelImageSlice32bitMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImageSlice32bitMatrixBuffer))+", "+str(channelImageSlice32bitMatrixBuffer.getDimension()))
    channelImage8bitUnsignedSliceMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight()], NativeTypeEnum.UnsignedByte); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
    #print("channelImage8bitUnsignedSliceMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(channelImage8bitUnsignedSliceMatrixBuffer))+", "+str(channelImage8bitUnsignedSliceMatrixBuffer.getDimension()))
    clij2_instance.copy(channelImageSlice32bitMatrixBuffer, channelImage8bitUnsignedSliceMatrixBuffer);

    #Calculate 24 bit pixels from 8 bit buffer and pixel value formula
    sliceMatrixBuffer24Bit = clij2_instance.create([grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight()], NativeTypeEnum.UnsignedInt) #Conversion floats to integers
    #print("sliceMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(sliceMatrixBuffer24Bit))+", "+str(sliceMatrixBuffer24Bit.getDimension()))
    clij2_instance.multiplyImageAndScalar(channelImage8bitUnsignedSliceMatrixBuffer, sliceMatrixBuffer24Bit, totalCoefficient)
    #colouredChannelMatrix = clij2_instance.pullMatXYZ(matrixBuffer24Bit)
    #print("colouredChannelMatrix: "+str(colouredChannelMatrix))

    #Transpose matrix24bit
    transposedMatrixBuffer24Bit = clij2_instance.create([grayLevelImagePlus.getHeight(), grayLevelImagePlus.getWidth()], NativeTypeEnum.UnsignedInt)
    #print("transposedMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(transposedMatrixBuffer24Bit))+", "+str(transposedMatrixBuffer24Bit.getDimension()))
    #clij2_instance.transposeYZ(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)
    #clij2_instance.transposeXZ(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)
    clij2_instance.transposeXY(sliceMatrixBuffer24Bit, transposedMatrixBuffer24Bit)

    #Reshape slice matrix
    reshapedChannelImageSliceUnsignedIntegerMatrixBuffer = clij2_instance.create([grayLevelImagePlus.getWidth()*grayLevelImagePlus.getHeight(), 1], NativeTypeEnum.UnsignedInt)
    #print("reshapedChannelImageSliceUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer))+", "+str(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.getDimension()))
    #clij2_instance.copy(transposedMatrixBuffer24Bit, reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    clij2_instance.copy(sliceMatrixBuffer24Bit, reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)

    #Extract matrix from buffer
    reshapedSliceContainer = clij2_instance.pullMat(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    #reshapedSliceContainer = clij2_instance.pullMatXYZ(reshapedChannelImageSliceUnsignedIntegerMatrixBuffer)
    #print("reshapedSliceContainer: "+str(reshapedSliceContainer))

    #Set pixels to image
    imagePluses = []
    for sliceMatrix in reshapedSliceContainer:
        #print("sliceMatrix: "+str(sliceMatrix))
        sliceImage = IJ.createImage("RGB Channel "+str(0)+" slice"+str(zDepthNumber), "RGB Black", grayLevelImagePlus.getWidth(), grayLevelImagePlus.getHeight(), 1)
        sliceProcessor = sliceImage.getProcessor()
        sliceProcessor.setPixels(sliceMatrix)
        sliceImage.setProcessor(sliceProcessor)
        imagePluses.append(sliceImage)
    #print("imagePluses: "+str(imagePluses))
    realColouredChannelImage = imagePluses[0]
    realColouredChannelImageProcessor = realColouredChannelImage.getProcessor()
    channelImageRGBstack_3rd_try.addSlice(realColouredChannelImageProcessor)

    #Close every buffer
    reshapedChannelImageSliceUnsignedIntegerMatrixBuffer.close()
    sliceMatrixBuffer24Bit.close()
    transposedMatrixBuffer24Bit.close()
    channelImage8bitUnsignedSliceMatrixBuffer.close()
    channelImageSlice32bitMatrixBuffer.close()

#Convert stack to ImagePlus
colouredChannelImage_3rd_try = ImagePlus(String("Processed image with CLIJ buffers, Z separation beforehand"), channelImageRGBstack_3rd_try)
colouredChannelImage_3rd_try.show()

# clean
clij2_instance.clear()
