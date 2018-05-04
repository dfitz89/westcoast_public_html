<?php
/*
Plugin Name: WCS Test Plugin
Plugin URI: http://www.westcoastsoftware.com/plugin-info
Description: Displays Bio of post author
Author: Dan Fitzgerald
Version: 1.0
Author URI: http://www.westcoastsoftware.com/
*/
//function myPluginFunction(){
//function code will go here
//}

//add author function
function addAuthor($text) {
/*the $text var picks up content from hook filter*/
//check if author has a url, a first name and last name.
//if not, no "Find out more" link will be displayed
//and just the required nickname will be used.
if (get_the_author_meta('user_url')){
$bioUrl = "<a href='".get_the_author_meta('user_url')."'>
Find Out More</a>";
}
if (get_the_author_meta('first_name')
&& get_the_author_meta('last_name')){
$bioName = get_the_author_meta('first_name').
" ".get_the_author_meta('last_name');
}else{
$bioName = get_the_author_meta('nickname');
}
//check if author has a description, if not
//then, no author bio is displayed.
if (get_the_author_meta('description')){
$bio = "<div class='authorName'>by <strong>".$bioName."</strong>
<div class='authorBio'>"
.get_the_author_meta('description')." ".$bioUrl."
</div>
</div>";
}else{
$bio = "<div class='authorName'>
by <strong>".$bioName."</strong>
</div>";
}
//returns the post content
//and prepends the bio to the top of the content
return $bio.$text;
}//addAuthor
//calls the post content and runs the function on it.
if (is_page(73))
	add_filter('the_content', 'addAuthor');

// Some CSS to position for the paragraph
function authorCSS() {
//These variables set the url and directory paths:
$authorStyleUrl =
WP_PLUGIN_URL . '/wcs_test/authover.css';
$authorStyleFile =
WP_PLUGIN_DIR . '/wcs_test/authover.css';
//if statement checks that file does exist
if ( file_exists($authorStyleFile) ) {
//registers and evokes the stylesheet
wp_register_style('authorStyleSheet', $authorStyleUrl);
wp_enqueue_style( 'authorStyleSheet');
}
}
//evoke the authorCSS function on WordPress initialization
add_action('init', 'authorCSS');

// this function includes the jQuery plugin and makes sure that jQuery min version 1.4.2 is loaded up if jQuery hasn't been registered on the site yet. If it has, it won't register it again
function addjQuery() {

    wp_enqueue_script('authover',
 		WP_PLUGIN_URL . '/wcs_test/jquery.authover.js',
 		array('jquery'), '1.4.2' );      
}

/*this fn will add the jQuery script that accesses the full jQuery plugin
it's normally recomended to add all scripts in using the wp_enqueue_script
but this is so small and custom, it won't conflict with anything else
so it's ok*/
function addAuthorHover(){

	echo '<script type="text/javascript">
jQuery(function(){
	jQuery(".authorName").authorHover();
});
</script>';
}

add_action('init', 'addjQuery');
add_action('wp_head', 'addAuthorHover');
//add_filter('the_title', 'myPluginFunction');
//or you could:
/*add_action('wp_head', 'myPluginFunction');*/
?>