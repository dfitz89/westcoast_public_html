// JavaScript Document
function testCallBackFunction(a) {
	alert("inside testCallBackFunction a = " + a);
}

 var jsReady = false;
 function isReady() {
	 return jsReady;
 }
 function pageInit() {
	 jsReady = true;
	 document.forms["form1"].output.value += "\n" + "JavaScript is ready.\n";
 }
 function thisMovie(movieName) {
	 if (navigator.appName.indexOf("Microsoft") != -1) {
		 return window[movieName];
	 } else {
		 return document[movieName];
	 }
 }
 function sendToActionScript(value) {
	 alert(value);
	 thisMovie("ExternalInterfaceExample").sendToActionScript(value);
 }
 function sendToJavaScript(value) {
	 document.forms["form1"].output.value += "ActionScript says: " + value + "\n";
 }
