	var RecaptchaOptions = {
	   theme : 'blackglass',
	   tabindex : 6
	};

	function checkForm()
	{
	    var cname, cemail, csubject, cmessage, csecuritycode;
	    with(window.document.msgform)
	    {
		   cname    = name;
		   cemail   = email;
		   csubject = subject;
		   cmessage = message;
		   csecuritycode = recaptcha_response_field;
	    }
//		alert("recaptcha_response_field value = " + csecuritycode);
	
	    if(trim(cname.value) == '')
	    {
		   alert('Please enter your name');
		   cname.focus();
		   return false;
	    }
	    else if(trim(csubject.value) == '')
	    {
		   alert('Please enter message subject');
		   csubject.focus();
		   return false;
	    }
	    else if(trim(cemail.value) == '')
	    {
		   alert('Please enter your email');
		   cemail.focus();
		   return false;
	    }
	    else if(!isEmail(trim(cemail.value)))
	    {
		   alert('Email address is not valid');
		   cemail.focus();
		   return false;
	    }
	    else if(trim(cmessage.value) == '')
	    {
		   alert('Please enter your message');
		   cmessage.focus();
		   return false;
	    }
		else if(trim(csecuritycode.value) == '')
		{
		   alert('Please enter the Anti-Spam security code');
		   csecuritycode.focus();
		   return false;
		}
	    else
	    {
		   cname.value    = trim(cname.value);
		   cemail.value   = trim(cemail.value);
		   csubject.value = trim(csubject.value);
		   cmessage.value = trim(cmessage.value);
		   csecuritycode.value = trim(csecuritycode.value);
		   return true;
	    }
	}
	
	function trim(str)
	{
	   return str.replace(/^\s+|\s+$/g,'');
	}
	
	function isEmail(str)
	{
	   var regex = /^[-_.a-z0-9]+@(([-_a-z0-9]+\.)+(ad|ae|aero|af|ag|ai|al|am|an|ao|aq|ar|arpa|as|at|au|aw|az|ba|bb|bd|be|bf|bg|bh|bi|biz|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|com|coop|cr|cs|cu|cv|cx|cy|cz|de|dj|dk|dm|do|dz|ec|edu|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gh|gi|gl|gm|gn|gov|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|in|info|int|io|iq|ir|is|it|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|mg|mh|mil|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|museum|mv|mw|mx|my|mz|na|name|nc|ne|net|nf|ng|ni|nl|no|np|nr|nt|nu|nz|om|org|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|pro|ps|pt|pw|py|qa|re|ro|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|sk|sl|sm|sn|so|sr|st|su|sv|sy|sz|tc|td|tf|tg|th|tj|tk|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|um|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)|(([0-9][0-9]?|[0-1][0-9][0-9]|[2][0-4][0-9]|[2][5][0-5])\.){3}([0-9][0-9]?|[0-1][0-9][0-9]|[2][0-4][0-9]|[2][5][0-5]))$/i;
	
		return regex.test(str);
	}