<?php

/**************************************************************************
ADMIN INITIALIZE
**************************************************************************/

if ('wcs-qrc-options.php' == basename($_SERVER['SCRIPT_FILENAME']))
{
	die ('Please do not access this admin file directly. Thanks!');
}


if (!is_admin()) {die('This plugin is only accessible from the WordPress Dashboard.');}


if (!defined('WP_CONTENT_DIR'))	define('WP_CONTENT_DIR', ABSPATH . 'wp-content');
if (!defined('WP_CONTENT_URL'))	define('WP_CONTENT_URL', get_option('siteurl') . '/wp-content');
if (!defined('WP_ADMIN_URL'))	define('WP_ADMIN_URL', get_option('siteurl') . '/wp-admin');
if (!defined('WP_PLUGIN_DIR'))	define('WP_PLUGIN_DIR', WP_CONTENT_DIR . '/plugins');
if (!defined('WP_PLUGIN_URL'))	define('WP_PLUGIN_URL', WP_CONTENT_URL . '/plugins');

?>


<div class="wrap">
	<table width="600" border="0" cellspacing="0" cellpadding="0">
		<tr>
			<td>&nbsp;</td>
			<td>&nbsp;</td>
		</tr>

		<tr>
			<td colspan="2"><img width="600" height="128" src="<?php _e(WP_PLUGIN_URL); ?>/wcs-qr-code-generator/images/wcs-qrc-header.png" border="0" alt="WCS QR Code Generator Options" title="WCS QR Code Generator Options" /></td>
		</tr>

		<tr>
			<td><br/>&nbsp;<iframe src="http://www.facebook.com/plugins/like.php?href=http%3A%2F%2Fwww.wpcodesnippets.info%2Fblog%2Fwcs-qr-code-generator.html&amp;layout=standard&amp;show_faces=true&amp;width=450&amp;action=like&amp;font=lucida+grande&amp;colorscheme=light&amp;height=80" scrolling="no" frameborder="0" style="border:none; overflow:hidden; width:450px; height:80px;" allowTransparency="true"></iframe></td>
			<td>&nbsp;</td>
		</tr>
	</table>


	<table cellpadding="0" cellspacing="0" border="0" style="width:600px; margin-left:5px; color:black; background:#F6F6F6; border:1px solid #606060; padding:4px; -moz-border-radius:10px; -webkit-border-radius:10px; border-radius:10px;">
	<tr><td>

		<h2>&nbsp;About this Plug-in</h2>
		<div style="margin-left:20px; line-height:150%; font-size:14px;">
		This plugin is a <b>QR Code</b> (Quick Response) generator for <b>mobile tagging</b>. It allows you to create one of the ever-popular QR Code images anywhere on a page/post or in a text widget. A <b>simple shortcode</b> defaults to generating the 2d code for the current page/post.<br/><br/>

		Plus, <b>attributes allow you to set</b> the: size, color, url, tooltip, image format (png or jpg), and error correction level ... along with an option to use a shortened url. The url attribute can be utilized instead as an email address, plain text, phone number, vcard, sms, <i>etc</i>.
		<br/><br/>
		</div>



		<h2>&nbsp;Links Related to this Plug-in</h2>
		<div style="margin-left:20px; line-height:150%; font-size:14px;">
		<ol style="margin-left:40px;">
			<li>Visit our web site, <a target="_blank" href="http://wpcodesnippets.INFO">wpCodeSnippets.INFO</a>, for lots of WordPress tips, tweaks, shortcodes, and plugins.</li>
			<li>View the prototype <a target="_blank" href="http://wpcodesnippets.info/blog/how-to-add-qr-codes-to-your-blog.html">source code</a> explanation for this plug-in. This page also includes a variety of useful information regarding QR Codes.</li>
			<li>View <a target="_blank" href="http://wpcodesnippets.info/blog/wcs-qr-code-generator.html">details for this plug-in</a> at our web site.</li>
			<li>Revisit the <a target="_blank" href="http://wordpress.org/extend/plugins/wcs-qr-code-generator/">plug-in download</a> page at the WordPress repository. In the sidebar on the right, click your "<b>My Rating</b>" preference (hopefully 5 stars).</li>
			<li>Did you find this plug-in useful? A small <a target="_blank" href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&currency_code=USD&business=LukeAmerica2020%40gmail.com&item_name=WP%20Code%20Snippets%20donation&amount=0.00&image_url=http://wpcodesnippets.info/files/paypal_header.png">donation</a> will support our continued WordPress development efforts. Enter any amount.</li>
		</ol>
		<br/>
		</div>


		<h2>&nbsp;Shortcode Usage Information</h2>
		<div style="margin-left:20px; line-height:150%; font-size:14px;">
		Upon activation of this plug-in, you'll have access to a <b>new shortcode</b> that generates QR Code images. In its default usage, a QR Code is generated for the current page/post. Additionally, you can use the shortcode anywhere on a page/post or in a text widget.<br/><br/>

		<b>Basic Usage Syntax:</b><br/>
		<div style="margin-left:25px;">[wcs_qr_code]</div>
		<br/>

		<b>Example Usage:</b><br/>
		<div style="margin-left:25px;">
			[wcs_qr_code <b>url=</b>'now is the time' <b>size=</b>'128' <b>color=</b>'darkblue']<br/>
		</div>
		<br/>

		<b>Available Attributes:</b><br/>
		<ol style="margin-left:40px;">
			<li><b>url</b> is the content for the qr code image (defaults to the current page/post url)<br/>-- <i>more on this below</i></li>
			<li><b>size</b> is square image's size in pixels (default is '100')</li>
			<li><b>color</b> can be a 6-digit hex color value or an HTML color name (default is 'black')<br/></li>
			<li><b>ecl</b> is the error correction level (default is 'L|4')<br/>-- <i>more on this below</i><br/></li>
			<li><b>shorten</b> is a toggle for shortening the url (default is 'false')<br/></li>
			<li><b>format</b> is the image format (PNG or JPG) (default is 'png')<br/></li>
			<li><b>tooltip</b> is the image's tooltip text (default is none)<br/></li>
		</ol>
		<br/>

		<b>ECL Details:</b><br/>
		<div style="margin-left:25px;">
			This plug-in utilizes the <a href="http://code.google.com/apis/chart/image/docs/gallery/qr_codes.html" target="_blank">Google Charts API</a>. You can view the various ECL settings <a href="http://code.google.com/apis/chart/image/docs/gallery/qr_codes.html#details" target="_blank">here</a>.<br/><br/>

			Essentially, the ECL code consists of two components: (1) the error correction level (L, M, Q, or H), and (2) the white border row/column width (1 - 40 rows, not pixels).
		</div>
		<br/>

		<b>URL Details:</b><br/>
		<div style="margin-left:25px;">
			If omitted, the URL defaults to the current page/post url. You can also use any valid url or text (within the character limitation of the selected ECL attribute value).<br/><br/>

			When using an <b>email address</b>, a standard format is expected. For example <b>me@here.com</b> should be implemented as <b>mailto:me@here.com</b>.<br/><br/>

			<b>Telephone numbers</b> also have a standardized format. For example, <b>212-555-1212</b> should be implemented as <b>tel:+12125551212</b>.<br/><br/>

			An <b>SMS link</b> is encoded in a fashion similar to an email address. For example, a link to the number <b>12345</b> should be implemented as <b>sms:12345</b>.<br/><br/>

			These and many other possibilities are explained in detail <a href="http://code.google.com/p/zxing/wiki/BarcodeContents" target="_blank">here</a>.<br/>
		</div>
		<br/>

		<h2>&nbsp;Additional References</h2>
		<div style="margin-left:20px; line-height:150%; font-size:14px;">
			Here's a site that DECODES a QR image to verify the data:<br/>
			<a href="http://zxing.org/w/decode.jspx" target="_blank">http://zxing.org/w/decode.jspx</a>.<br/><br/>

			This <a href="http://wpcodesnippets.info/blog/how-to-add-qr-codes-to-your-blog.html" target="_blank">page</a> offers a variety of information regarding QR Codes.<br/><br/>

			Here are a few sites that let you download a QR Code reader for your mobile device.<br/>
			<ol style="margin-left:40px;">
				<li><a href="http://www.i-nigma.mobi/" target="_blank">i-nigma.mobi</a></li>
				<li><a href="http://reader.kaywa.com/" target="_blank">kaywa.com</a></li>
				<li><a href="http://get.neoreader.com/" target="_blank">neoreader.com</a></li>
				<li><a href="http://www.quickmark.com.tw/En/basic/index.asp" target="_blank">quickmark.com.tw</a></li>
			</ol>
			<br/>
		</div>

	</td></tr>
	</table>
</div>
<br/><br/>
