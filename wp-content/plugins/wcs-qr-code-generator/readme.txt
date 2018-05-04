=== WCS QR Code Generator ===

Contributors:		LukeAmerica2020
Plugin URI:		http://wpcodesnippets.info/blog/wcs-qr-code-generator.html
Tags:			qr code, barcode, 2d, qr, mobile tagging, mobile, qurify, shortcode, widget, generate, generator, wp code snippets, wpCodeSnippets.info, Luke America, LukeAmerica2020
Author URI:		http://wpCodeSnippets.INFO
Author:			WP Code Snippets (Luke America)
Donate link:		http://wpcodesnippets.info/site-info/support-our-efforts.html
Requires at least:	2.9.0
Tested up to:		3.1.2
Stable tag:		1.0

This plugin is a QR Code (Quick Response) image generator for mobile tagging.

== Description ==

This plugin is a **QR Code** (Quick Response) generator for **mobile tagging**. It allows you to create one of the ever-popular QR Codes anywhere on a page/post or in a text widget. A **simple shortcode** defaults to generating the 2d code for the current page/post.

Plus, **attributes allow** you to set the: size, color, url (or email, text, phone number, vcard, sms, etc.), tooltip, image format (png or jpg), and error correction level ... along with an option to use a shortened url.

More details are available under *Installation* (above) and at Dashboard->WCS-QR-Code (after activation).

== Installation ==

**Basic Plug-in Usage:**

Install and activate the plug-in. Use the **shortcode** [wcs_qr_code] anywhere in a post/page or in a text widget to generate a QR Code image.

**Standard WordPress installation procedure:**

1. Download the ZIP file to your local computer.
1. Unzip the file's contents.
1. Login as an administrator to your WordPress website.
1. Upload the `wcs-qr-code-generator` directory to your `/wp-content/plugins/` directory.
1. Activate the plugin through the WordPress Dashboard->Plugins menu.

**Basic Shortcode Usage syntax:**

[wcs_qr_code]

**Example Shortcode Usage:**

[wcs_qr_code **url=**'now is the time' **size=**'128' **color=**'darkblue']

**Shortcode Usage Information:**

1. **url** is the content for the qr code image (defaults to the current page/post url) -- *more on this below*
1. **size** is square image's size in pixels (default is '100')
1. **color** can be a 6-digit hex color value or an HTML color name (default is 'black')
1. **ecl** is the error correction level (default is 'L|4') -- *more on this below*
1. **shorten** is a toggle for shortening the url (default is 'false')
1. **format** is the image format (PNG or JPG) (default is 'png')
1. **tooltip** is the image's tooltip text (default is none)

**ECL Details:**

This plug-in utilizes the Google Charts API. You can view the various ECL settings [here](http://code.google.com/apis/chart/image/docs/gallery/qr_codes.html#details "Google Charts API").

Essentially, the ECL code consists of two components: (1) the error correction level (L, M, Q, or H), and (2) the white border row/column width (1 - 40 rows, not pixels).

**URL Details:**

If omitted, the URL defaults to the current page/post url. You can also use any valid url or text (within the character limitation of the selected ECL attribute value).

When using an **email address**, a standard format is expected. For example **me&#64;here.com** should be implemented as **mailto:me&#64;here.com**.

**Telephone numbers** also have a standardized format. For example, **212-555-1212** should be implemented as **tel:+12125551212**.

An **SMS link** is encoded in a fashion similar to an email address. For example, a link to the number **12345** should be implemented as **sms:12345**.

These and many other possibilities are explained in detail [here](http://code.google.com/p/zxing/wiki/BarcodeContents "2D Barcode Contents").

== Changelog ==

= 1.0 =
* 2011-05-09
* official public plugin release

= 0.9.0 =
* 2011-02-19 *(cut/paste prototype functions)*
* prototype release

== Upgrade Notice ==

= 1.0 =
You can now implement this QR Code image generation functionality as a plug-in.

== Additional Information ==

* View [details for this plug-in](http://wpcodesnippets.info/blog/wcs-qr-code-generator.html "Plug-in Landing Page") at our web site.

* View the full [source code](http://wpcodesnippets.info/blog/how-to-add-qr-codes-to-your-blog.html "Source Code Details") explanation for the prototype of this plug-in. This page also includes a variety of useful information regarding QR Codes.

* Visit our web site, [wpCodeSnippets.INFO](http://wpcodesnippets.INFO "WP Code Snippets"), for lots of WordPress tips, tweaks, shortcodes, and plugins.

* This plug-in is released under the GNU General Public License (GPL2). No external services are required and there are no additional features to purchase.

== Donations ==

Did you find this plug-in useful? A small [donation](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&currency_code=USD&business=LukeAmerica2020%40gmail.com&item_name=WP%20Code%20Snippets%20donation&amount=0.00&image_url=http://wpcodesnippets.info/files/paypal_header.png "Support Future Development") will be much appreciated AND it supports our continued WordPress development efforts. Enter any amount.


== Frequently Asked Questions ==

= Will this plug-in work on multi-sites? =
Yes. Just use Network Activate. Visit your Dashboard. Click *Network Admin* at the top right. Click *Plugins* in the sidebar menu. Locate *WCS QR Code Generator* in the list. Then, click *Network Activate*.

= Where can I get a QR Code reader? =
1. [online decoder](http://zxing.org/w/decode.jspx) -- for verification of image data
1. [i-nigma.mobi](http://www.i-nigma.mobi/)
1. [kaywa.com](http://reader.kaywa.com/)
1. [neoreader.com](http://get.neoreader.com/)
1. [quickmark.com.tw](http://www.quickmark.com.tw/En/basic/index.asp)

= Other questions? =
Leave [questions, comments, and suggestions](http://wpcodesnippets.info/blog/wcs-custom-permalinks-hotfix.html "Plug-in Landing Page") at our web site's plug-in landing page.

= What languages are available? =
Currently, only English is available. Future updates may include additional languages (for the Dashboard information page).

= Can I help? =
Sure! We're in regular need of testers. We have several plug-in prototypes under development at our website. In addition, we could always use help with translations for internationalization.

Visit our website: [wpCodeSnippets.INFO](http://wpcodesnippets.INFO "Visit Our Website").

== Screenshots ==

1. This is a screen shot of a portion of the Dashboard information page added by this plug-in.

