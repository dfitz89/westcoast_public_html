/*
	UIZE JAVASCRIPT FRAMEWORK 2012-01-10

	http://www.uize.com/reference/Uize.Widget.Captcha.Recaptcha.html
	Available under MIT License or GNU General Public License -- http://www.uize.com/license.html
*/
Uize.module({name:'Uize.Widget.Captcha.Recaptcha',required:'Uize.Comm.Script',builder:function(d_a){var d_b=d_a.subclass(null,function(){var d_c=this;d_c.d_d=Uize.Comm.Script({callbackMode:'client'});d_c.initializeCaptcha();}),d_e=d_b.prototype;d_e.initializeCaptcha=function(){var d_c=this;if(!(d_c.recaptchaObject=window.Recaptcha)&&d_c.d_f)d_c.d_d.request({url:[d_c.d_f],returnType:'json',requestMethod:'GET',callback:function(){(d_c.recaptchaObject=window.Recaptcha)?d_c.recaptchaObjectCreate():d_c.callInherited('inform')({state:'error',message:d_c.localize('loadingError')});}});else d_c.recaptchaObjectCreate();};d_e.recaptchaObjectCreate=function(){var d_c=this;d_c.recaptchaObject&&d_c.recaptchaObject.create(d_c.d_g,d_c.get('idPrefix'),{theme:'clean'});};d_e.validate=function(d_h){var d_c=this,d_i=d_h.callback,d_j=d_c.recaptchaObject;d_c.d_d.set({callbackMode:'server'});d_c.d_d.request({url:[d_c.d_k,{recaptcha_response_field:d_j.get_response(),recaptcha_challenge_field:d_j.get_challenge()}],returnType:'json',
requestMethod:'GET',callback:function(d_l){d_c.set({isValid:d_l&&d_l.isValid});if(!d_c.get('isValid'))d_c.recaptchaObjectCreate();Uize.isFunction(d_i)&&d_i(d_l);}});};d_e.wireUi=function(){var d_c=this;if(!d_c.isWired){d_a.prototype.wireUi.call(d_c);}};d_b.registerProperties({d_f:'loadingUrl',d_k:'validationUrl',d_g:'key'});return d_b;}});