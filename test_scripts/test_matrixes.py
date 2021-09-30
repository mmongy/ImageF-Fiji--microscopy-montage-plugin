import os, sys
from sys import path
import time
import java, jarray, array
from ij import IJ
from net.haesleinhuepf.clij.clearcl import ClearCLBuffer
from net.haesleinhuepf.clij.coremem.enums import NativeTypeEnum
from net.haesleinhuepf.clij2 import CLIJ2

IJ.log('\\Clear') #efface le contenu de la console

#test32bitMatrix = [array.array('i', [1,2,3,4,5,6,7,8,9]), array.array('i', [11,12,13,14,15,16,17,18,19]), array.array('i', [21,22,23,24,25,26,27,28,29])]
test32bitMatrix = [1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,21,22,23,24,25,26,27,28,29]
print("test32bitMatrix: "+str(test32bitMatrix))
javatest32bitMatrix = array.array('i', test32bitMatrix)
print("javatest32bitMatrix: "+str(javatest32bitMatrix))

# init GPU
clij2_instance = CLIJ2.getInstance()

#Conversion 32bit to 8bit
test32bitMatrixBuffer = clij2_instance.pushMatXYZ(javatest32bitMatrix)
#clij2_instance.print(test32bitMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'
test8bitUnsignedMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(test32bitMatrixBuffer), NativeTypeEnum.UnsignedByte); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
clij2_instance.copy(test32bitMatrixBuffer, test8bitUnsignedMatrixBuffer);
clij2_instance.print(test8bitUnsignedMatrixBuffer)


#Trying a pixel by pixel multiplication
totalCoefficient = float(0.5)
testMatrixBuffer24Bit = clij2_instance.create(clij2_instance.getDimensions(test32bitMatrixBuffer))
clij2_instance.print(testMatrixBuffer24Bit)
clij2_instance.multiplyImageAndScalar(test8bitUnsignedMatrixBuffer, testMatrixBuffer24Bit, totalCoefficient)


#Conversion floats to integers
testUnsignedIntegerMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(test32bitMatrixBuffer), NativeTypeEnum.UnsignedInt); #https://github.com/clij/clij-coremem/blob/master/src/main/java/net/haesleinhuepf/clij/coremem/enums/NativeTypeEnum.java
clij2_instance.copy(testMatrixBuffer24Bit, testUnsignedIntegerMatrixBuffer)
#clij2_instance.print(testUnsignedIntegerMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'


#Reshape matrix
reshapedTestIntegerMatrixBuffer = clij2_instance.create(clij2_instance.getDimensions(test32bitMatrixBuffer), NativeTypeEnum.UnsignedInt)
clij2_instance.copy(testUnsignedIntegerMatrixBuffer, reshapedTestIntegerMatrixBuffer)
#clij2_instance.print(reshapedTestIntegerMatrixBuffer) #java.util.UnknownFormatConversionException: java.util.UnknownFormatConversionException: Conversion = 'Cannot convert image of type UnsignedInt'


#Extract matrix

print("test32bitMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(test32bitMatrixBuffer)))
#javaOriginallyPushedTest32bitMatrix = clij2_instance.pullMatXYZ(test32bitMatrixBuffer)
javaOriginallyPushedTest32bitMatrix = clij2_instance.pullMat(test32bitMatrixBuffer)
print("javaOriginallyPushedTest32bitMatrix: "+str(javaOriginallyPushedTest32bitMatrix))

print("test8bitUnsignedMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(test8bitUnsignedMatrixBuffer)))
#javaTest8bitUnsignedMatrix = clij2_instance.pullMatXYZ(test8bitUnsignedMatrixBuffer)
javaTest8bitUnsignedMatrix = clij2_instance.pullMat(test8bitUnsignedMatrixBuffer)
print("javaTest8bitUnsignedMatrix: "+str(javaTest8bitUnsignedMatrix))

print("testMatrixBuffer24Bit dimensions: "+str(clij2_instance.getDimensions(testMatrixBuffer24Bit)))
#javaTestMatrixBuffer24Bit = clij2_instance.pullMatXYZ(testMatrixBuffer24Bit)
javaTestMatrixBuffer24Bit = clij2_instance.pullMat(testMatrixBuffer24Bit)
print("javaTestMatrixBuffer24Bit: "+str(javaTestMatrixBuffer24Bit))

print("testUnsignedIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(testUnsignedIntegerMatrixBuffer)))
#javaTestUnsignedIntegerMatrix = clij2_instance.pullMatXYZ(testUnsignedIntegerMatrixBuffer)
javaTestUnsignedIntegerMatrix = clij2_instance.pullMat(testUnsignedIntegerMatrixBuffer)
print("javaTestUnsignedIntegerMatrix: "+str(javaTestUnsignedIntegerMatrix))

print("reshapedTestIntegerMatrixBuffer dimensions: "+str(clij2_instance.getDimensions(reshapedTestIntegerMatrixBuffer)))
#javaReshapedTestIntegerMatrix = clij2_instance.pullMatXYZ(reshapedTestIntegerMatrixBuffer) # I tried both of them
javaReshapedTestIntegerMatrix = clij2_instance.pullMat(reshapedTestIntegerMatrixBuffer)
print("javaReshapedTestIntegerMatrix: "+str(javaReshapedTestIntegerMatrix)) # When i try to re

for item in range(len(javaReshapedTestIntegerMatrix)):
    imageMatrix = javaReshapedTestIntegerMatrix[item]
    print("loopedImageMatrix: "+str(imageMatrix))

#CLose all
test32bitMatrixBuffer.close()
test8bitUnsignedMatrixBuffer.close()
testMatrixBuffer24Bit.close()
testUnsignedIntegerMatrixBuffer.close()
reshapedTestIntegerMatrixBuffer.close()

# clean
clij2_instance.clear()
