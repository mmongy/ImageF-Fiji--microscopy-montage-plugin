
/* global OlySlider, OlySplash, MEUtil */

function startTutorial() {
	var _specCB = document.getElementById("specimenCB");
	var _gammaSldr = new OlySlider("gammaSlider");
	var _imagePaths = ["images/astrocytescolorpc.jpg","images/blackknotcolor.jpg",
		"images/computerchipcolordic.jpg","images/crownwart.jpg",
		"images/favabeanmitosiscolorfl.jpg","images/parameciumcolorpc.jpg",
		"images/oleanderleafcolor.jpg","images/petrifiedwoodcolorpol.jpg",
		"images/pineneedlecolor.jpg","images/benzamidefiberscolor.jpg",
		"images/tubercolor.jpg","images/ratnervescolor.jpg",
		"images/ptk2microtubulescolor.jpg","images/youngstarfishcolor.jpg",
		"images/wildsilk3color.jpg","images/woodsection.jpg"];
	var _splash = OlySplash(initialize, _imagePaths);
	var _specimenCan = document.getElementById("specimenCan");
	var _specimenCtx = _specimenCan.getContext("2d");
	var _specimenImgData = _specimenCtx.getImageData(0,0,175,175);
	var _graphGridCtx = MEUtil.upscaleCanvas("graphGridCan").getContext("2d");
	var _graphCtx = MEUtil.upscaleCanvas("graphCan").getContext("2d");
	var _imgIndex = 0;
	var _cbSelect = document.getElementById("specimenCB");
	var _gammaSldrLbl = document.getElementById("gammaSldrLbl");

	function initialize() {
		addListeners();
		initControls();

		var randNum = (Math.random() * 16) >> 0;
		initRandImg(randNum);
		drawGrid(_graphGridCtx);

		MEUtil.raf(enterFrameHandler);
		_splash.fadeOut();
	}

	function addListeners() {
		_specCB.onchange = function() {
			_imgIndex = this.selectedIndex;
			changeImg(_imgIndex);
			_gammaSldr.setPosition(0.275);
		};
	}

	function initControls() {
		_gammaSldr.setPosition(0.275);
	}

	function initRandImg(randNum) {
		_imgIndex = randNum;
		_cbSelect.selectedIndex = _imgIndex;
		changeImg(_imgIndex);
	}

	function changeImg(index) {
		var img = new Image();

		img.onload = function() {
			_specimenCtx.drawImage(img, 0, 0, 175, 175);
			_specimenImgData = _specimenCan.getContext("2d").getImageData(0, 0, 175, 175);
		};
		img.setAttribute("crossorigin", "Anonymous");
		img.src = _imagePaths[index];
	}

	function enterFrameHandler() {
		if (_gammaSldr.hasChanged) {
			_gammaSldr.hasChanged = false;

			var pos = _gammaSldr.getPosition(),
				val = (pos * 80) | 0,
				gammaVal = val == 22 ? 1 : 0.45 + 2.05 * val / 80;

			correctGamma(gammaVal);
			updateLbl(gammaVal);
			updateGraph(gammaVal);
		}

		MEUtil.raf(enterFrameHandler); // DO NOT MOVE; LEAVE AS LAST STATEMENT
	}

	function drawGrid(ctx) {
		// var scale = 0;
		ctx.fillStyle = "rgba(127, 127, 127, 0.7)";
		ctx.clearRect(0, 0, 177, 177);
		ctx.beginPath();

		for (var i = 17.6; i < 175; i += 17.6) {
			// scale = i;
			ctx.fillRect(i, 0, 2, 177);
			ctx.fillRect(0, i, 177, 2);
		}
	}

	function updateGraph(gammaCorrectionVal) {
		var scale = 177 / 255,
			xCoord = 0, yCoord = 0;

		_graphCtx.clearRect(0,0,177,177);
		_graphCtx.beginPath();

		for (var i = 0; i < 256; i++) {
			xCoord = i * scale;
			yCoord = -((Math.pow(i / 255, gammaCorrectionVal) * 255) * scale);
			_graphCtx.lineTo(xCoord, yCoord + 177);
		}
		_graphCtx.stroke();
	}

	function correctGamma(gammaCorrectionVal) {
		var imgData = _specimenCan.getContext("2d").getImageData(0, 0, 175, 175),
			data = imgData.data,
			specData = _specimenImgData.data,
			intensityR = 0, intensityG = 0, intensityB = 0,
			r = 0, g = 0, b = 0;

		for (var i = 0; i < specData.length; i += 4) {
			intensityR = specData[i] / 255;
			intensityG = specData[i + 1] / 255;
			intensityB = specData[i + 2] / 255;

			r = Math.pow(intensityR, gammaCorrectionVal) * 255;
			g = Math.pow(intensityG, gammaCorrectionVal) * 255;
			b = Math.pow(intensityB, gammaCorrectionVal) * 255;

			data[i] = r;
			data[i + 1] = g;
			data[i + 2] = b;
		}

		_specimenCtx.putImageData(imgData,0,0);
	}

	function updateLbl(gammaVal) {
		var val = (((gammaVal * 100) | 0) / 100) + "";

		if (val.length < 3) {
			val += ".0";
		}

		_gammaSldrLbl.innerHTML = "Gamma Correction: " + val;
	}
}

// \/ NO TOUCHY \/
$(document).ready(startTutorial);
