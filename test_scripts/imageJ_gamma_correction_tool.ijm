// Gamma correction Tool
//
// This tool macro provides a gamma adjustment tool
// that remaps the LUT using the selected gamma value
// This preserves the pixel values, unlike the
// built-in Process>Math>Gamma function, which 
// remaps the pixel values. 
// Drag the mouse in the gamma diagram to adjust.
// Or use the tool's option dialog, which you open
// by double-clicking on the tool icon.

var a=newArray(261);
var b=newArray(261);
var r=newArray(256);
var gamma=1;

macro 'Gamma correction Tool- C000T4b12Y' {
    if (bitDepth==24) exit ("Non RGB image expected");
    x2=0;y2=0;
    w=minOf(getWidth,getHeight)*0.5;
    while(true) {
        getCursorLoc(x, y, z, flags);
        if (flags&16==0) exit();
        if((x>w)||(y>w)) { x=w-1;y=1;}
        if ((x2!=x)||(y2!=y)) {
            gamma=(w-x)/y;
            createGammaLUT(gamma);
            x2=x;y2=y;
        }
    }
}

macro 'Gamma correction Tool Options' {
  gamma = getNumber("Gamma:",gamma);
  w=minOf(getWidth,getHeight)*0.5;
  createGammaLUT(gamma) ;
}

function createGammaLUT(gamma) {
 for (i=0; i<256; i++) {
   r[i] = pow(i/255, 1/gamma)*255;
   a[i]=i/(255/w);
   b[i]=w-r[i]/(255/w);
 }
 setLut(r,r,r);
 a[255]=w; a[256]=0;a[257]=0;a[258]=w;a[259]=w;a[260]=0;
 b[255]=0;b[256]=0;b[257]=w;b[258]=0;b[259]=w;b[260]=w;
 makeSelection('freeline', a, b);
 showStatus('Gamma: '+d2s(gamma,2));
}