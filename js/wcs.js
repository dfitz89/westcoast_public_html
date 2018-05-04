function checkLoginForm() {
	var valid = true;
//	alert("inside checkLoginForm...")
	var f = document.forms['loginForm'];
	
	if(document.getElementById('userId').value.length==0)
	{
		alert("Username cannot be blank");
		valid=false;
	}
	else if(document.getElementById('password').value.length==0)
	{
		alert("Password cannot be blank");
		valid=false;
	}
//	alert("valid = " + valid);
	return valid;
}

function logout() {
//		alert("inside logout...");
		// In the varArray are all the variables you want to give with the function
//		var varArray = new Array();
//		varArray[0] = "var1";
//		varArray[1] = "var2";
	   
		// the url which you have to reload is this page, but you add an action to the GET- or POST-variable
//	var url="index.php?action=logout&vars="+varArray;
	var url="http://www.westcoastsoftware.com/index.php?action=logout";
		//alert("url =>"+ url + "<");
		
		// Opens the url in the same window
		   window.open(url, "_self");
}