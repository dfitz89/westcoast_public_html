<?php
/*
Plugin Name:	WCS QR Code Generator
Version:	1.0
Plugin URI:	http://wpcodesnippets.info/blog/wcs-qr-code-generator.html
Download URI:	http://wordpress.org/extend/plugins/wcs-qr-code-generator/
Author:		WP Code Snippets (Luke America)
Author URI:	http://wpCodeSnippets.INFO
Author Email:	LukeAmerica2020@gmail.com
Contributors:	Luke America (LukeAmerica2020)
License:	GNU General Public License (GPL2)
Tags:		qr code, barcode, 2d, qr, mobile tagging, mobile, qurify, shortcode, widget, generate, generator, wp code snippets, wpCodeSnippets.info, Luke America, LukeAmerica2020
Description:	This plugin is a QR Code (Quick Response) generator for mobile tagging. It allows you to create one of the ever-popular QR Codes anywhere on a page/post or in a text widget. A simple shortcode defaults to generating the 2d code for the current page/post. Plus, attributes allow you to set the: size, color, url (or email, text, phone number, vcard, sms, etc.), tooltip, image format (png or jpg), and error correction level ... along with an option to use a shortened url. More details are available in the readme.txt file and (after activation) at Dashboard->WCS-QR-Code.
*/


/*
	WCS QR Code Generator
	Copyright (c) 2011 WP Code Snippets / Gizmo Digital Fusion (LukeAmerica2020@gmail.com)

	This program is free software; you can redistribute it and/or modify it
	under the terms of the GNU General Public License as published by the
	Free Software Foundation; either version 2 of the License, or (at your
	option) any later version.

	This program is distributed in the hope that it will be useful, but WITHOUT
	ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
	FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
	more details.

	You should have received a copy of the GNU General Public License along
	with this program, LICENSE.txt. If not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA. Or, visit this web address:
	http://www.gnu.org/licenses/gpl.html OR http://www.gnu.org/licenses/gpl-2.0.html.
*/




/**************************************************************************
ACTIVATE / ENABLE PLUGIN
**************************************************************************/


// prevent file from being accessed directly
$wcsp_qrc_filname = 'wcs-qr-code-generator.php';
if (basename($_SERVER['SCRIPT_FILENAME']) == $wcsp_qrc_filname)
{
	die ("Please do not access this file, $wcsp_qrc_filname, directly. Thanks!");
}


// enable plugin
wcsp_qrc_enable();




/**************************************************************************
PLUGIN FUNCTIONS
**************************************************************************/


function wcsp_qrc_enable()
{
	// activate plugin admin features
	register_activation_hook(__FILE__, 'wcsp_qrc_activate_admin_options');

	// enable shortcode feature
	add_shortcode('wcs_qr_code', 'wcsp_qr_code_shortcode_handler');

	// enable shortcodes in text widgets
	add_filter('widget_text', 'do_shortcode');
}


// shortcode handler
function wcsp_qr_code_shortcode_handler($atts)
{
	$parms = shortcode_atts(array(
		'size' => '100',
		'color' => '',
		'ecl' => 'L|4',
		'url' => '',
		'shorten' => '0',
		'format' => 'png',
		'tooltip' => '',),
		$atts);

	$size = $parms['size'];
	$color = $parms['color']; // can be a hex color value or an html color name
	$ecl = $parms['ecl'];
	$url = $parms['url'];
	$shorten = $parms['shorten'];
	$tooltip = $parms['tooltip'];

	$format = strtolower($parms['format']);
	if ($format != 'png') {$format = 'jpg';}

	// process shorten (t/f) option
	$b_shorten = false;
	if (($shorten == 'yes') || ($shorten == 'y') || ($shorten == 'true') || ($shorten == '1'))
	{$b_shorten = 1;}

	return wcsp_qr_code_generator($size, $color, $ecl, $url, $b_shorten, $format, $tooltip);
}


// qr code generator
function wcsp_qr_code_generator($size=100, $color='', $ecl='L|4', $url='', $shorten=0, $format='png', $tooltip='')
{
	// $ecl reference:		http://code.google.com/apis/chart/docs/gallery/qr_codes.html#details
	// data coding specifics:	http://code.google.com/p/zxing/wiki/BarcodeContents

	// get url/text parameter
	$this_url = $url;

	// if url is empty, get current web page url
	if ($this_url == '')
	{
		// get the current url
		$this_url = 'http';
		if ($_SERVER["HTTPS"] == "on") {$this_url .= "s";}
		$this_url .= "://";
		if ($_SERVER["SERVER_PORT"] != "80")
		{
			$this_url .= $_SERVER["SERVER_NAME"] . ":" . $_SERVER["SERVER_PORT"] . $_SERVER["REQUEST_URI"];
		}
		else
		{
			$this_url .= $_SERVER["SERVER_NAME"] . $_SERVER["REQUEST_URI"];
		}
	}

	// shorten a valid url
	if (($shorten==1) && (wcsp_qr_is_valid_url($this_url)==1))
	{
		$this_url = file_get_contents("http://tinyurl.com/api-create.php?url=" . $this_url);
	}

	// encode url
	$this_url = urlencode($this_url);

	// construct the image url
	$img_url = 'http://chart.apis.google.com/chart?cht=qr&chld=' . $ecl . '&chs=' . $size . 'x' . $size . '&chl=';
	$img_url .= $this_url;

	// convert black to jpg, if requested
	if (($format == 'jpg') && ($color == '')) {$color = '#000000';}

	// translate possible HTML color name
	$color = wcsp_qr_color_name_to_hex($color);

	// change the color, if requested
	if ((strlen($color) == '6') || (strlen($color) == '7'))
	{
		// init images
		$src = imageCreateFromPng($img_url);
		$w = imageSX($src);
		$h = imageSY($src);
		$dest = imageCreateTrueColor($w, $h);

		// strip off # in hex color and get rgb array of values
		$new_color = $color;
		if (strlen($new_color) == 7)
		{
			$new_color = substr($new_color, -6, 6);
		}
		$new_color_array = wcsp_qr_rgb_to_array(hexdec($new_color));

		// scan src image pixels and set dest image pixels
		for ($x = 0; $x < $w; $x++)
		{
			for ($y = 0; $y < $h; $y++)
			{
				$src_pix = imageColorAt($src, $x, $y);
				$src_pix_array = wcsp_qr_rgb_to_array($src_pix);

				// image returned by google has black pixels set (0,0,0)
				if ($src_pix_array[0] == 0 && $src_pix_array[1] == 0 && $src_pix_array[2] == 0)
				{
					$src_pix_array[0] = $new_color_array[0];
					$src_pix_array[1] = $new_color_array[1];
					$src_pix_array[2] = $new_color_array[2];
				}
				imageSetPixel($dest, $x, $y, imageColorAllocate($dest, $src_pix_array[0], $src_pix_array[1], $src_pix_array[2]));
			}
		}

		// start output buffering
		ob_start();

		if ($format == 'png') {imagePng($dest);}
		else {imageJpeg($dest);}

		$contents =  ob_get_contents();
		ob_end_clean();

		// complete image processing
		if ($format == 'png')
		{
			$img_url = 'data:image/png;base64,' . base64_encode($contents);
		}
		else
		{
			$img_url = 'data:image/jpeg;base64,' . base64_encode($contents);
		}
		imageDestroy($src);
		imageDestroy($dest);
	}

	// construct output HTML
	$output = '<img src="' . $img_url . '" width="' . $size . '" height="' . $size . '"';
	if ($tooltip) {$output .= ' title="' . $tooltip . '"';}
	$output .= ' />';

	// exit
	return $output;
}


// convert an RGB color into three hue array components
function wcsp_qr_rgb_to_array($rgb)
{
	$a_colors[0] = ($rgb >> 16) & 0xFF;
	$a_colors[1] = ($rgb >> 8) & 0xFF;
	$a_colors[2] = $rgb & 0xFF;
	return $a_colors;
}


// convert an html color name to a hex color value
// if the input is not a color name, the original value is returned
function  wcsp_qr_color_name_to_hex($color_name)
{
	// standard 147 HTML color names
	$colors  =  array(
		'aliceblue'=>'F0F8FF',
		'antiquewhite'=>'FAEBD7',
		'aqua'=>'00FFFF',
		'aquamarine'=>'7FFFD4',
		'azure'=>'F0FFFF',
		'beige'=>'F5F5DC',
		'bisque'=>'FFE4C4',
		'black'=>'000000',
		'blanchedalmond '=>'FFEBCD',
		'blue'=>'0000FF',
		'blueviolet'=>'8A2BE2',
		'brown'=>'A52A2A',
		'burlywood'=>'DEB887',
		'cadetblue'=>'5F9EA0',
		'chartreuse'=>'7FFF00',
		'chocolate'=>'D2691E',
		'coral'=>'FF7F50',
		'cornflowerblue'=>'6495ED',
		'cornsilk'=>'FFF8DC',
		'crimson'=>'DC143C',
		'cyan'=>'00FFFF',
		'darkblue'=>'00008B',
		'darkcyan'=>'008B8B',
		'darkgoldenrod'=>'B8860B',
		'darkgray'=>'A9A9A9',
		'darkgreen'=>'006400',
		'darkgrey'=>'A9A9A9',
		'darkkhaki'=>'BDB76B',
		'darkmagenta'=>'8B008B',
		'darkolivegreen'=>'556B2F',
		'darkorange'=>'FF8C00',
		'darkorchid'=>'9932CC',
		'darkred'=>'8B0000',
		'darksalmon'=>'E9967A',
		'darkseagreen'=>'8FBC8F',
		'darkslateblue'=>'483D8B',
		'darkslategray'=>'2F4F4F',
		'darkslategrey'=>'2F4F4F',
		'darkturquoise'=>'00CED1',
		'darkviolet'=>'9400D3',
		'deeppink'=>'FF1493',
		'deepskyblue'=>'00BFFF',
		'dimgray'=>'696969',
		'dimgrey'=>'696969',
		'dodgerblue'=>'1E90FF',
		'firebrick'=>'B22222',
		'floralwhite'=>'FFFAF0',
		'forestgreen'=>'228B22',
		'fuchsia'=>'FF00FF',
		'gainsboro'=>'DCDCDC',
		'ghostwhite'=>'F8F8FF',
		'gold'=>'FFD700',
		'goldenrod'=>'DAA520',
		'gray'=>'808080',
		'green'=>'008000',
		'greenyellow'=>'ADFF2F',
		'grey'=>'808080',
		'honeydew'=>'F0FFF0',
		'hotpink'=>'FF69B4',
		'indianred'=>'CD5C5C',
		'indigo'=>'4B0082',
		'ivory'=>'FFFFF0',
		'khaki'=>'F0E68C',
		'lavender'=>'E6E6FA',
		'lavenderblush'=>'FFF0F5',
		'lawngreen'=>'7CFC00',
		'lemonchiffon'=>'FFFACD',
		'lightblue'=>'ADD8E6',
		'lightcoral'=>'F08080',
		'lightcyan'=>'E0FFFF',
		'lightgoldenrodyellow'=>'FAFAD2',
		'lightgray'=>'D3D3D3',
		'lightgreen'=>'90EE90',
		'lightgrey'=>'D3D3D3',
		'lightpink'=>'FFB6C1',
		'lightsalmon'=>'FFA07A',
		'lightseagreen'=>'20B2AA',
		'lightskyblue'=>'87CEFA',
		'lightslategray'=>'778899',
		'lightslategrey'=>'778899',
		'lightsteelblue'=>'B0C4DE',
		'lightyellow'=>'FFFFE0',
		'lime'=>'00FF00',
		'limegreen'=>'32CD32',
		'linen'=>'FAF0E6',
		'magenta'=>'FF00FF',
		'maroon'=>'800000',
		'mediumaquamarine'=>'66CDAA',
		'mediumblue'=>'0000CD',
		'mediumorchid'=>'BA55D3',
		'mediumpurple'=>'9370D0',
		'mediumseagreen'=>'3CB371',
		'mediumslateblue'=>'7B68EE',
		'mediumspringgreen'=>'00FA9A',
		'mediumturquoise'=>'48D1CC',
		'mediumvioletred'=>'C71585',
		'midnightblue'=>'191970',
		'mintcream'=>'F5FFFA',
		'mistyrose'=>'FFE4E1',
		'moccasin'=>'FFE4B5',
		'navajowhite'=>'FFDEAD',
		'navy'=>'000080',
		'oldlace'=>'FDF5E6',
		'olive'=>'808000',
		'olivedrab'=>'6B8E23',
		'orange'=>'FFA500',
		'orangered'=>'FF4500',
		'orchid'=>'DA70D6',
		'palegoldenrod'=>'EEE8AA',
		'palegreen'=>'98FB98',
		'paleturquoise'=>'AFEEEE',
		'palevioletred'=>'DB7093',
		'papayawhip'=>'FFEFD5',
		'peachpuff'=>'FFDAB9',
		'peru'=>'CD853F',
		'pink'=>'FFC0CB',
		'plum'=>'DDA0DD',
		'powderblue'=>'B0E0E6',
		'purple'=>'800080',
		'red'=>'FF0000',
		'rosybrown'=>'BC8F8F',
		'royalblue'=>'4169E1',
		'saddlebrown'=>'8B4513',
		'salmon'=>'FA8072',
		'sandybrown'=>'F4A460',
		'seagreen'=>'2E8B57',
		'seashell'=>'FFF5EE',
		'sienna'=>'A0522D',
		'silver'=>'C0C0C0',
		'skyblue'=>'87CEEB',
		'slateblue'=>'6A5ACD',
		'slategray'=>'708090',
		'slategrey'=>'708090',
		'snow'=>'FFFAFA',
		'springgreen'=>'00FF7F',
		'steelblue'=>'4682B4',
		'tan'=>'D2B48C',
		'teal'=>'008080',
		'thistle'=>'D8BFD8',
		'tomato'=>'FF6347',
		'turquoise'=>'40E0D0',
		'violet'=>'EE82EE',
		'wheat'=>'F5DEB3',
		'white'=>'FFFFFF',
		'whitesmoke'=>'F5F5F5',
		'yellow'=>'FFFF00',
		'yellowgreen'=>'9ACD32');

	$color_name = strtolower($color_name);
	if (isset($colors[$color_name]))
	{
		return ('#' . $colors[$color_name]);
	}
	else
	{
		return ($color_name);
	}
}


// test if URL is valid (for URL shortening), ie, ONLY shorten url's
function wcsp_qr_is_valid_url($url)
{
	return preg_match('|^http(s)?://[a-z0-9-]+(.[a-z0-9-]+)*(:[0-9]+)?(/.*)?$|i', $url);
}




/**************************************************************************
ENABLE ADMIN OPTIONS
**************************************************************************/

function wcsp_qrc_options() {include 'wcs-qrc-options.php';}


function wcsp_qrc_activate_admin_options()
{
	global $current_user;

	$wcs_qrc_icon_url = plugins_url('wcs-qr-code-generator/images/wcs-qrc-icon.png');

	if (current_user_can('manage_options')) // typically Admin or Super-Admin
	{
		// at the bottom of all Dashboard menus (also has a custom icon)
	        add_menu_page('WCS-QR-Code', 'WCS-QR-Code', 2, 'wcsp_qrc_options', 'wcsp_qrc_options', $wcs_qrc_icon_url);

		// OR:
		// inside Settings menu block
		//add_submenu_page('options-general.php', 'WCS-QR-Code', 'WCS-QR-Code', 2, 'WCS-QR-Code', 'wcsp_qrc_options');
	}
}

add_action('admin_menu', 'wcsp_qrc_activate_admin_options');

?>
