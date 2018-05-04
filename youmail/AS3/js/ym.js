// JavaScript Document
    var jsReady = false;

    function isReady() {
//		alert("inside isReady");
        return jsReady;
    }

    function pageInit() {
//		alert("inside pageInit");
        jsReady = true;
        document.forms["form1"].output.value += "\n" + "JavaScript is ready.\n";
    }

    function thisMovie(movieName) {
//		alert("inside thisMovie = " + movieName);
        if (navigator.appName.indexOf("Microsoft") != -1) {
//			alert("here");
            return window[movieName];
        } else {
//			alert("here1");
            return document[movieName];
        }
    }

    function doSave() {
		var movie = thisMovie("YMAudioRecorderAS3");
	    var flvRecordingId = movie.getFlvRecordingId();
		if (flvRecordingId != 'undefined' && flvRecordingId != null)
	        movie.doSave(status, flvRecordingId);
		else
			alert("Problem with Saving Recording");
    }
	

	/**
	 * Call this method in order to reset the Flash Recorder
	 */
	function resetRecorder() {
		var movie = thisMovie("YMAudioRecorderAS3");
		movie.resetRecorder();
	}

	/**
	 * This method invokes doCancel action script function on the recorder
	 */
    function doCancel() {
		var result = confirm("Are you sure you want to Cancel?");
		if (result)
		{
			var movie = thisMovie("YMAudioRecorderAS3");
	//		alert("movie = " + movie);
		    var flvRecordingId = movie.getFlvRecordingId();
			movie.doCancel("User cancelled recording...", flvRecordingId);
		}
    }
	
	function enableDisableSaveButton(value) {
		//alert("value = " + value);
		if (value == "true")
			document.getElementById('saveButton').disabled = true;
		if (value == "false")
			document.getElementById('saveButton').disabled = false;
	}
	
	function enableDisableCancelButton(value) {
		//alert("value = " + value);
		if (value == "true")
			document.getElementById('cancelButton').disabled = true;
		if (value == "false")
			document.getElementById('cancelButton').disabled = false;
	}
	
    function doChangeBackgroundColor(color) {
		var movie = thisMovie("YMAudioRecorderAS3");
//		alert("movie = " + movie + " and color = " + color);
        movie.doChangeBackgroundColor(color);
    }
	
    function doChangeVolumeDisplayBackgroundColor(color) {
		var movie = thisMovie("YMAudioRecorderAS3");
//		alert("movie = " + movie + " and color = " + color);
        movie.doChangeVolumeDisplayBackgroundColor(color);
    }
	
	function doShowLogo() {
		var movie = thisMovie("YMAudioRecorderAS3");
		var showLogo = get_radio_value();
//		alert("movie = " + movie + " and showLogo = " + showLogo);
        movie.doShowLogo(showLogo);
	}
	
	function displayXmlConfigFileNotLoadedMsg(msg) {
//	    alert("inside displayXmlConfigFileNotLoadedMsg ...msg = " + msg);
		var movie = thisMovie("YMAudioRecorderAS3");
//		alert("movie = " + movie);
        movie.displayXmlConfigFileNotLoadedMsg(msg);
	}
    
    function callFromAS_XmlNotLoaded(msg) {
	    alert(msg);
		displayXmlConfigFileNotLoadedMsg(msg);
//    	return "From javascript doCancel...";
    }

	// Only used if cancel button exposed in Flash recorder
    function callFromAS_DoCancel(str) {
	    alert(str);
    	return "From javascript doCancel...";
    }
    
    var globalSequence = 1;
    var fileName = "recording" + generateRandomFileNumber();
    
    function generateRandomFileNumber() {
    	var randomNumber = (globalSequence++) + '-' + Math.floor(Math.random() * 99999);
    	return randomNumber;
    }
	
	function get_radio_value() {
		var rad_val;
		for (var i=0; i < document.recorderForm.showLogo.length; i++)
		{
		   if (document.recorderForm.showLogo[i].checked)
      	   {
      	   		rad_val = document.recorderForm.showLogo[i].value;
//				alert("rad_val = " + rad_val);
      	   }
		}
		return rad_val;
	}

	function showHideConfigPanel(element) {
		var btnLabel = document.getElementById('configPanelBtnLabel');
		if (element.style.visibility == "hidden")
		{
			element.style.visibility = "visible";
			btnLabel.innerHTML = 'Hide Config Panel';
		}
		else
		{
			element.style.visibility = "hidden";
			btnLabel.innerHTML = 'Show Config Panel';
		}
	}