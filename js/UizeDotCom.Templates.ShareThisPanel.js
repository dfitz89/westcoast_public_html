/*
	UIZE Web Site 2012-01-10

	http://www.uize.com/reference/UizeDotCom.Templates.ShareThisPanel.html
	Available under MIT License or GNU General Public License -- http://www.uize.com/license.html
*/
Uize.module({name:'UizeDotCom.Templates.ShareThisPanel',required:['Uize.Url','Uize.Xml'],builder:function(){var _a=function(){};_a.process=function(input){var output=[];function _b(_c,_d,_e,_f){output.push('\r\n	<!-- ',_c,' -->\r\n		<a target="_blank" href="',Uize.Xml.toAttributeValue(Uize.Url.resolve(_d,_e)),'" class="shareThisLink ',_f,'">',_c,'...</a>');}output.push('\r\n<div id="page-shareThisPanel" class="shareThisPanel">\r\n	<div class="shareThisHeading">Share This Using...</div>');_b('Personal E-mail','mailto:',{subject:'Check this out',body:input.title+'\n\n'+input.url},'email');_b('Facebook','http://www.facebook.com/share.php',{t:input.title,u:input.url},'facebook');_b('Twitter','http://twitter.com/home',{status:'Check out '+input.title+' over @uize '+input.url},'twitter');_b('StumbleUpon','http://www.stumbleupon.com/submit',{title:input.title,url:input.url},'stumbleUpon');_b('del.icio.us','http://del.icio.us/post',{title:input.title,url:input.url},'delicious');_b('Digg','http://digg.com/submit',{
phase:2,title:input.title,url:input.url},'digg');_b('Reddit','http://reddit.com/submit',{title:input.title,url:input.url},'reddit');_b('FriendFeed','http://friendfeed.com/',{title:input.title,url:input.url},'friendFeed');_b('MySpace','http://www.myspace.com/Modules/PostTo/Pages/',{t:input.title,u:input.url},'mySpace');_b('Google Bookmarks','http://www.google.com/bookmarks/mark',{op:'edit',title:input.title,bkmk:input.url,label:input.keywords,annotation:input.description},'google');_b('LinkedIn','http://www.linkedin.com/shareArticle',{mini:true,title:input.title,url:input.url,summary:input.description,source:'uize.com'},'linkedIn');_b('Mixx','http://www.mixx.com/submit',{mini:true,title:input.title,page_url:input.url},'mixx');_b('Technorati','http://technorati.com/faves',{add:input.url},'technorati');_b('Posterous','http://posterous.com/share',{linkto:input.url},'posterous');_b('Plurk','http://plurk.com/',{status:input.url},'plurk');_b('Ping.fm','http://ping.fm/ref/',{method:'microblog',title:input.title,
link:input.url},'pingFm');_b('Diigo','http://www.diigo.com/post',{title:input.title,url:input.url},'diigo');_b('Faves','http://faves.com/Authoring.aspx',{t:input.title,u:input.url},'faves');_b('Mister Wong','http://www.mister-wong.com/index.php',{action:'addurl',bm_description:input.title,bm_url:input.url},'misterWong');_b('dzone','http://www.dzone.com/links/add.html',{action:'addurl',title:input.title,url:input.url,description:input.description},'dzone');_b('Connotea','http://www.connotea.org/addpopup',{'continue':'confirm',title:input.title,uri:input.url},'connotea');output.push('\r\n	<div class="shareThisFooter"></div>\r\n</div>\r\n\r\n');return output.join('');};_a.input={title:'string',url:'string'};return _a;}});