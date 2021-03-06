/*
	This is an automatically generated module, compiled from the JavaScript template file:
		UizeDotCom.Templates.ShareThisPanel.js.jst
*/

/*ScruncherSettings Mappings="=" LineCompacting="TRUE"*/

Uize.module ({
	name:'UizeDotCom.Templates.ShareThisPanel',
	required:[
		'Uize.Url',
		'Uize.Xml'
	],
	builder:function () {
		var _package = function () {};

		/*** Public Static Methods ***/
			_package.process = function (input) {
				var output = [];
				 function _shareLink (_serviceName,_linkPrefix,_linkParams,_linkClass) {
				output.push ('\r\n	<!-- ',_serviceName,' -->\r\n		<a target="_blank" href="',Uize.Xml.toAttributeValue (Uize.Url.resolve (_linkPrefix,_linkParams)),'" class="shareThisLink ',_linkClass,'">',_serviceName,'...</a>');
				 }
				output.push ('\r\n<div id="page-shareThisPanel" class="shareThisPanel">\r\n	<div class="shareThisHeading">Share This Using...</div>');

					_shareLink (
						'Personal E-mail',
						'mailto:',
						{
							subject:'Check this out',
							body:input.title + '\n\n' + input.url
						},
						'email'
					);
					_shareLink (
						'Facebook',
						'http://www.facebook.com/share.php',
						{
							t:input.title,
							u:input.url
						},
						'facebook'
					);
					_shareLink (
						'Twitter',
						'http://twitter.com/home',
						{
							status:'Check out ' + input.title + ' over @uize ' + input.url
						},
						'twitter'
					);
					_shareLink (
						'StumbleUpon',
						'http://www.stumbleupon.com/submit',
						{
							title:input.title,
							url:input.url
						},
						'stumbleUpon'
					);
					_shareLink (
						'del.icio.us',
						'http://del.icio.us/post',
						{
							title:input.title,
							url:input.url
						},
						'delicious'
					);
					_shareLink (
						'Digg',
						'http://digg.com/submit',
						{
							phase:2,
							title:input.title,
							url:input.url
						},
						'digg'
					);
					_shareLink (
						'Reddit',
						'http://reddit.com/submit',
						{
							title:input.title,
							url:input.url
						},
						'reddit'
					);
					_shareLink (
						'FriendFeed',
						'http://friendfeed.com/',
						{
							title:input.title,
							url:input.url
						},
						'friendFeed'
					);
					_shareLink (
						'MySpace',
						'http://www.myspace.com/Modules/PostTo/Pages/',
						{
							t:input.title,
							u:input.url
						},
						'mySpace'
					);
					_shareLink (
						'Google Bookmarks',
						'http://www.google.com/bookmarks/mark',
						{
							op:'edit',
							title:input.title,
							bkmk:input.url,
							label:input.keywords,
							annotation:input.description
						},
						'google'
					);
					_shareLink (
						'LinkedIn',
						'http://www.linkedin.com/shareArticle',
						{
							mini:true,
							title:input.title,
							url:input.url,
							summary:input.description,
							source:'uize.com'
						},
						'linkedIn'
					);
					_shareLink (
						'Mixx',
						'http://www.mixx.com/submit',
						{
							mini:true,
							title:input.title,
							page_url:input.url
						},
						'mixx'
					);
					_shareLink (
						'Technorati',
						'http://technorati.com/faves',
						{
							add:input.url
						},
						'technorati'
					);
					_shareLink (
						'Posterous',
						'http://posterous.com/share',
						{
							linkto:input.url
						},
						'posterous'
					);
					_shareLink (
						'Plurk',
						'http://plurk.com/',
						{
							status:input.url
						},
						'plurk'
					);
					_shareLink (
						'Ping.fm',
						'http://ping.fm/ref/',
						{
							method:'microblog',
							title:input.title,
							link:input.url
						},
						'pingFm'
					);
					_shareLink (
						'Diigo',
						'http://www.diigo.com/post',
						{
							title:input.title,
							url:input.url
						},
						'diigo'
					);
					_shareLink (
						'Faves',
						'http://faves.com/Authoring.aspx',
						{
							t:input.title,
							u:input.url
						},
						'faves'
					);
					_shareLink (
						'Mister Wong',
						'http://www.mister-wong.com/index.php',
						{
							action:'addurl',
							bm_description:input.title,
							bm_url:input.url
						},
						'misterWong'
					);
					_shareLink (
						'dzone',
						'http://www.dzone.com/links/add.html',
						{
							action:'addurl',
							title:input.title,
							url:input.url,
							description:input.description
						},
						'dzone'
					);
					_shareLink (
						'Connotea',
						'http://www.connotea.org/addpopup',
						{
							'continue':'confirm',
							title:input.title,
							uri:input.url
						},
						'connotea'
					);

				output.push ('\r\n	<div class="shareThisFooter"></div>\r\n</div>\r\n\r\n');
				return output.join ('');
			};

		/*** Public Static Properties ***/
			_package.input = {
				title:'string',
				url:'string'
			};

		return _package;
	}
});

