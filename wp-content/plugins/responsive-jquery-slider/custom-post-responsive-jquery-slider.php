<?php
// Registers the new post type and taxonomy
function custom_post_responsive_slider() { 
	$labels = array(
		'name' 				 => __('Sliders', 'responsive-jquery-slider'),
		'singular_name'		 => __('Slider', 'responsive-jquery-slider'),
		'add_new'			 => __('Add New', 'responsive-jquery-slider'),
		'add_new_item'		 => __('Add New Slider', 'responsive-jquery-slider'),
		'edit_item'			 => __('Edit Slider', 'responsive-jquery-slider'),
		'new_item' 		 	 => __('New Slider', 'responsive-jquery-slider'),
		'view_item' 		 => __('View Slider', 'responsive-jquery-slider'),
		'search_items' 		 => __('Search Slider', 'responsive-jquery-slider'),
		'not_found'		 	 =>  __('Not Found', 'responsive-jquery-slider'),
		'not_found_in_trash' => __('Not Found in Trash', 'responsive-jquery-slider'),
		'parent_item_colon'  => '',
		'menu_name' 		 => __('Sliders', 'responsive-jquery-slider')
	);
	$args = array(
		'labels' 		       => $labels,
		'supports'             => array( 'editor' ),
		'public'		       => true,
		'public_queryable'     => true,
		'exclude_from_search'  => true,
		'show_ui'   		   => true,
		'query_var' 		   => true,
		'rewrite' 			   => false,
		'capability_type' 	   => 'post',
		'menu_icon' 		   => plugins_url( '/images/icon-slider.png' , __FILE__ ),
		'has_archive' 		   => false,
		'hierarchical' 		   => false,
		'menu_position' 	   => 5,
		'register_meta_box_cb' => 'rjs_slider_meta_box',
	);
	register_post_type( 'responsive-slider' , $args );
	flush_rewrite_rules();
}
add_action('init', 'custom_post_responsive_slider');


function rjs_slider_meta_box(){        
	add_meta_box('meta_box_slider', __('Configure your Slider', 'responsive-jquery-slider'), 'rjs_meta_box_meta_slider', 'responsive-slider', 'normal', 'high');
}

function rjs_Colorpicker(){ 
    wp_enqueue_style( 'wp-color-picker');
    wp_enqueue_script( 'wp-color-picker');
}
add_action('admin_enqueue_scripts', 'rjs_Colorpicker');

function rjs_meta_box_meta_slider(){
	global $post;
	
	$metaBoxC1 = get_post_meta($post->ID, 'valor_c1', true);
	$meta_element_align_c1 = get_post_meta($post->ID, 'custom_element_grid_align_meta_box_c1', true);
	$metaBoxSizeC1 = get_post_meta($post->ID, 'size_c1', true);
	$metaColorBackC1 = get_post_meta($post->ID, 'color_back_c1', true);
	$metaColorFontC1 = get_post_meta($post->ID, 'color_font_c1', true);
	
	$metaBoxC2 = get_post_meta($post->ID, 'valor_c2', true);
	$meta_element_align_c2 = get_post_meta($post->ID, 'custom_element_grid_align_meta_box_c2', true);
	$metaBoxSizeC2 = get_post_meta($post->ID, 'size_c2', true);
	$metaColorBackC2 = get_post_meta($post->ID, 'color_back_c2', true);
	$metaColorFontC2 = get_post_meta($post->ID, 'color_font_c2', true);
	
	$metaBoxC3 = get_post_meta($post->ID, 'valor_c3', true);
	$meta_element_align_c3 = get_post_meta($post->ID, 'custom_element_grid_align_meta_box_c3', true);
	$metaBoxSizeC3 = get_post_meta($post->ID, 'size_c3', true);
	$metaColorBackC3 = get_post_meta($post->ID, 'color_back_c3', true);
	$metaColorFontC3 = get_post_meta($post->ID, 'color_font_c3', true);
	
	$image_src = '';		
	$image_id = get_post_meta( $post->ID, '_image_id', true );
	$image_src = wp_get_attachment_url( $image_id );
	
	$args = array( 'numberposts' => -1, 'post_type' => array('post', 'page'), 'post_status' => 'publish' );
    $get_posts = get_posts( $args );
    $metaLoopPost = get_post_meta( $post->ID, 'custom_parent_loop', true);
    $metaLinkPer = get_post_meta($post->ID, 'link_per', true);
    $metaLinkName = get_post_meta($post->ID, 'link_name', true);
    $metaRange = get_post_meta($post->ID, 'chance', true);
    $metaColorButton = get_post_meta($post->ID, 'color_font_button', true);
    $metaTopButton = get_post_meta($post->ID, 'color_top_button', true);
    $metaBottomButton = get_post_meta($post->ID, 'color_bottom_button', true);
    $meta_element_target = get_post_meta($post->ID, 'custom_element_grid_target_meta_box', true);
	
    ?>
    <style type="text/css">
    #wp-fullscreen-body, #postdivrich, #preview-action{
    	display: none;
    }
    </style>
    <script type="text/javascript">
		jQuery(document).ready(function($) {
			$('#wp-fullscreen-body, #postdivrich, #preview-action').remove();
			$('.section_color').wpColorPicker();
			window.send_to_editor_default = window.send_to_editor;
			$('#set-book-image').click(function(){
				window.send_to_editor = window.attach_image;
				tb_show('', 'media-upload.php?post_id=<?php echo $post->ID ?>&amp;type=image&amp;TB_iframe=true');
				return false;
			});
			$('#remove-book-image').click(function() {
				$('.upload_image_id').val('');
				$('#book_image img').attr('src', '');
				$('#book_image img').hide();
				return false;
			});
			window.attach_image = function(html) {
				$('body').append('<div id="temp_image">' + html + '</div>');
				var img = $('#temp_image').find('img');
				imgurl   = img.attr('src');
				imgclass = img.attr('class');
				imgid    = parseInt(imgclass.replace(/\D/g, ''), 10);
				$('.upload_image_id').val(imgid);
				$('#book_image img').show();
				$('#remove-book-image').show();
				$('#book_image img').attr('src', imgurl);
				try{tb_remove();}catch(e){};
				$('#temp_image').remove();
				window.send_to_editor = window.send_to_editor_default;
			}
			$('#chanceSlider').on('change', function(){
			    $('#chance').val($('#chanceSlider').val());
			});

			$('#chance').on('keyup', function(){
			    $('#chanceSlider').val($('#chance').val());
			});
		});
	</script>

	<ul>
		<li style="display: block; width: 100%;">
			<label for="inputCap1" style="width:100%; float: left; font-weight: bold; padding: 0 0 10px 0;"><?php _e('Caption 1:', 'responsive-jquery-slider');?></label>
			<input style="width:85%; float: left; margin-right: 5px;" type="text" name="valor_c1" id="inputCap1" value="<?php echo $metaBoxC1;?>" />
			<select style="width: 12%; float: left;" name="custom_element_grid_align_c1" id="custom_element_grid_align_c1">
				<option value="left" <?php selected( $meta_element_align_c1, 'left' ); ?>><?php _e('Align left', 'responsive-jquery-slider');?></option>
				<option value="right" <?php selected( $meta_element_align_c1, 'right' ); ?>><?php _e('Align right', 'responsive-jquery-slider');?></option>
			</select>
			<div style="width: 100%; display: inline-block;">
				<label for="inputSizeCap1" style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Font Size:', 'responsive-jquery-slider');?></label>			
				<input style="width:8%; float: left; margin-right: 5px;" type="text" name="size_c1" id="inputSizeCap1" placeholder="27px" value="<?php if($metaBoxSizeC1 == null || $metaBoxSizeC1 == '27px'){ echo '27px'; }else{echo $metaBoxSizeC1;}?>" />
			</div>
			<label for="color_font_c1" style="width:100%; float: left; font-weight: bold;"><?php _e('Font Color', 'responsive-jquery-slider');?></label>
			<input name="color_font_c1" type="text" class="section_color" value="<?php if($metaColorFontC1 == null){ echo '#ffffff'; }else{echo $metaColorFontC1;}?>" data-default-color="#ffffff">
			<br />
			<label for="color_back_c1" style="width:100%; float: left; font-weight: bold;"><?php _e('Background Color', 'responsive-jquery-slider');?></label>
			<input name="color_back_c1" type="text" class="section_color" value="<?php if($metaColorBackC1 == null){ echo '#000000'; }else{echo $metaColorBackC1;}?>" data-default-color="#000000">
		</li>
		<hr />
		<li style="display: block; width: 100%;">
			<label for="inputCap2" style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Caption 2:', 'responsive-jquery-slider');?></label>
			<input style="width:85%; float: left; margin-right: 5px;" type="text" name="valor_c2" id="inputCap2" value="<?php echo $metaBoxC2;?>" />
			<select style="width: 12%; float: left;" name="custom_element_grid_align_c2" id="custom_element_grid_align_c2">
				<option value="left" <?php selected( $meta_element_align_c2, 'left' ); ?>><?php _e('Align left', 'responsive-jquery-slider');?></option>
				<option value="right" <?php selected( $meta_element_align_c2, 'right' ); ?>><?php _e('Align right', 'responsive-jquery-slider');?></option>
			</select>
			<div style="width: 100%; display: inline-block;">
				<label for="inputSizeCap2" style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Font Size:', 'responsive-jquery-slider');?></label>			
				<input style="width:8%; float: left; margin-right: 5px;" type="text" name="size_c2" id="inputSizeCap2" placeholder="22px" value="<?php if($metaBoxSizeC2 == null || $metaBoxSizeC2 == '22px'){ echo '22px'; }else{echo $metaBoxSizeC2;}?>" />
			</div>
			<label for="color_font_c2" style="width:100%; float: left; font-weight: bold;"><?php _e('Font Color', 'responsive-jquery-slider');?></label>
			<input name="color_font_c2" type="text" class="section_color" value="<?php if($metaColorFontC2 == null){ echo '#ffffff'; }else{echo $metaColorFontC2;}?>" data-default-color="#ffffff">
			<br />
			<label for="color_back_c2" style="width:100%; float: left; font-weight: bold;"><?php _e('Background Color', 'responsive-jquery-slider');?></label>
			<input name="color_back_c2" type="text" class="section_color" value="<?php if($metaColorBackC2 == null){ echo '#000000'; }else{echo $metaColorBackC2;}?>" data-default-color="#000000">
		</li>		
		<hr />
		<li style="display: block; width: 100%;">
			<label for="inputCap3" style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Caption 3:', 'responsive-jquery-slider');?></label>
			<input style="width:85%; float: left; margin-right: 5px;" type="text" name="valor_c3" id="inputCap3" value="<?php echo $metaBoxC3;?>" />
			<select style="width: 12%; float: left;" name="custom_element_grid_align_c3" id="custom_element_grid_align_c3">
				<option value="left" <?php selected( $meta_element_align_c3, 'left' ); ?>><?php _e('Align left', 'responsive-jquery-slider');?></option>
				<option value="right" <?php selected( $meta_element_align_c3, 'right' ); ?>><?php _e('Align right', 'responsive-jquery-slider');?></option>
			</select>
			<div style="width: 100%; display: inline-block;">
				<label for="inputSizeCap3" style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Font Size:', 'responsive-jquery-slider');?></label>			
				<input style="width:8%; float: left; margin-right: 5px;" type="text" name="size_c3" id="inputSizeCap3" placeholder="16px" value="<?php if($metaBoxSizeC3 == null || $metaBoxSizeC3 == '16px'){ echo '16px'; }else{echo $metaBoxSizeC3;}?>" />
			</div>
			<label for="color_font_c3" style="width:100%; float: left; font-weight: bold;"><?php _e('Font Color', 'responsive-jquery-slider');?></label>
			<input name="color_font_c3" type="text" class="section_color" value="<?php if($metaColorFontC3 == null){ echo '#ffffff'; }else{echo $metaColorFontC3;}?>" data-default-color="#ffffff">
			<br />
			<label for="color_back_c3" style="width:100%; float: left; font-weight: bold;"><?php _e('Background Color', 'responsive-jquery-slider');?></label>
			<input name="color_back_c3" type="text" class="section_color" value="<?php if($metaColorBackC3 == null){ echo '#000000'; }else{echo $metaColorBackC3;}?>" data-default-color="#000000">
		</li>	
		<hr />
		<li style="display: block; width: 100%;">
			<label style="width:100%; float: left; font-weight: bold; ; padding: 10px 0;" for="inputLinkName"><?php _e('Caption Button:', 'responsive-jquery-slider');?></label>
			<input style="width:100%; float: left; margin-right: 5px;" type="text" name="link_name" id="inputLinkName" value="<?php echo $metaLinkName;?>" />
		</li>
		<li style="display: block; width: 100%;">
			<div style="float: left; width: 40%; margin-right: 1%;">
				<label for="custom_parent" style="width:100%; float: left; font-weight: bold; ; padding: 10px 0;"><?php _e('Select the destiny - Post/Page', 'responsive-jquery-slider');?></label>
				
			    <select name="custom_parent" id="custom_parent">
			    	<option value=""><?php _e('- Select -', 'responsive-jquery-slider');?></option>
			    <?php foreach ( $get_posts as $parent_post )  { $url = get_permalink($parent_post->ID); ?>
			    	<option value="<?php echo get_permalink($parent_post->ID);?>" <?php if($metaLoopPost == $url){ echo' selected';};?>><?php echo $parent_post->post_title;?></option>
			    <?php } ;?>
			    </select>
			</div>
			<div style="float: left; width: 40%; margin-right: 1%;">
				<label style="width:100%; float: left; font-weight: bold; ; padding: 10px 0;" for="inputLinkPer"><?php _e('or personality the link:', 'responsive-jquery-slider');?></label>
			    <input style="width:100%; float: left; margin-right: 5px;" type="text" name="link_per" id="inputLinkPer" value="<?php echo $metaLinkPer;?>" />
			    <br />
				<em><?php _e("Attention! Don't Forget the <strong>http://</strong>", 'responsive-jquery-slider');?></em>
			</div>
			<div style="width: 17%; float: left;">
				<label style="width:100%; float: left; font-weight: bold; ; padding: 10px 0;" for="custom_element_grid_target"><?php _e('Open in:', 'responsive-jquery-slider');?></label>
				<select  style="width:100%;" name="custom_element_grid_target" id="custom_element_grid_target">
					<option value="self" <?php selected( $meta_element_target, 'self' ); ?>><?php _e('Same Page', 'responsive-jquery-slider');?></option>
					<option value="blank" <?php selected( $meta_element_target, 'blank' ); ?>><?php _e('New Page', 'responsive-jquery-slider');?></option>
				</select>
			</div>
		</li>
		<li style="display: block; width: 100%;">
			<label for="color_font_button" style="width:100%; float: left; font-weight: bold;"><?php _e('Font Color Button', 'responsive-jquery-slider');?></label>
			<input name="color_font_button" type="text" class="section_color" value="<?php if($metaColorButton == null){ echo '#ffffff'; }else{echo $metaColorButton;}?>" data-default-color="#ffffff">
			<br />
			<label for="color_top_button" style="width:100%; float: left; font-weight: bold;"><?php _e('Customize Gradient Button - Top', 'responsive-jquery-slider');?></label>
			<input name="color_top_button" type="text" class="section_color" value="<?php if($metaTopButton == null){ echo '#ffce79'; }else{echo $metaTopButton;}?>" data-default-color="#ffce79">
			<br />
			<label for="color_bottom_button" style="width:100%; float: left; font-weight: bold;"><?php _e('Customize Gradient Button - Bottom', 'responsive-jquery-slider');?></label>
			<input name="color_bottom_button" type="text" class="section_color" value="<?php if($metaBottomButton == null){ echo '#eeaf41'; }else{echo $metaBottomButton;}?>" data-default-color="#eeaf41">
			<br />
			<label style="width:100%; float: left; font-weight: bold;"><?php _e('Border Radius', 'responsive-jquery-slider');?></label>
			<input type="range" id="chanceSlider" class="vHorizon" min="0" max="10" step="1"  value="<?php if($metaRange == null){ echo '10'; }else{echo $metaRange;};?>" style="width: 20%;"><br/>
			<input type="text" name="chance" id="chance" class="text" value="<?php if($metaRange == null){ echo '10'; }else{echo $metaRange;};?>" style="width: 19.39%;">
		</li>
		<li style="display: block; width: 100%; margin-top: 10px;">
			<label style="width:100%; float: left; font-weight: bold; padding: 10px 0;"><?php _e('Slider Image:', 'responsive-jquery-slider');?></label><br />		
			<figure id="book_image" style="margin: 0;">
				<img src="<?php echo $image_src ?>" style="max-width:100%;<?php if($image_src == null){ echo' display: none;' ;} ?>" />
			</figure>
			<input type="hidden" name="upload_image_id" class="upload_image_id" value="<?php echo $image_id; ?>" />
			<p>
				<a title="<?php _e( 'Set slider image', 'responsive-jquery-slider' ) ?>" href="#" id="set-book-image" style="font-weight: bold; text-decoration: none;">+ <?php _e( 'Set slider image', 'responsive-jquery-slider' ) ?></a>
				<a title="<?php _e( 'Remove slider image', 'responsive-jquery-slider' ) ?>" href="#" id="remove-book-image" style="<?php echo ( ! $image_id ? 'display:none;' : '' ); ?> margin-left: 10px; font-weight: bold; text-decoration: none;">- <?php _e( 'Remove slider image', 'responsive-jquery-slider' ) ?></a>
			</p>
		</li>
	</ul>
	
	<?php

	}

add_action( 'save_post', 'rjs_save_slider_post', 1, 2 );

function rjs_save_slider_post( $post_id, $post ) {

  if ( empty( $post_id ) || empty( $post ) || empty( $_POST ) ) return;
  if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
  if ( is_int( wp_is_post_revision( $post ) ) ) return;
  if ( is_int( wp_is_post_autosave( $post ) ) ) return;
  if ( ! current_user_can( 'edit_post', $post_id ) ) return;
  if ( $post->post_type != 'responsive-slider' ) return;
 
  ////////////////////////////////////////////////////////////////////////////////////////////////
  //Caption 1////////////////////////////////////////////////////////////////////////////////////
  update_post_meta($post->ID, 'valor_c1', $_POST['valor_c1']);
  if(isset($_POST["custom_element_grid_align_c1"])){
    $meta_element_align_c1 = $_POST['custom_element_grid_align_c1'];
    update_post_meta($post->ID, 'custom_element_grid_align_meta_box_c1', $meta_element_align_c1);
  }
  update_post_meta($post->ID, 'size_c1', $_POST['size_c1']);
  update_post_meta($post->ID, 'color_font_c1', $_POST['color_font_c1']);
  update_post_meta($post->ID, 'color_back_c1', $_POST['color_back_c1']);
  ////////////////////////////////////////////////////////////////////////////////////////////////
  //Caption 2////////////////////////////////////////////////////////////////////////////////////
  update_post_meta($post->ID, 'valor_c2', $_POST['valor_c2']);
  if(isset($_POST["custom_element_grid_align_c2"])){
    $meta_element_align_c2 = $_POST['custom_element_grid_align_c2'];
    update_post_meta($post->ID, 'custom_element_grid_align_meta_box_c2', $meta_element_align_c2);
  }
  update_post_meta($post->ID, 'size_c2', $_POST['size_c2']);
  update_post_meta($post->ID, 'color_font_c2', $_POST['color_font_c2']);
  update_post_meta($post->ID, 'color_back_c2', $_POST['color_back_c2']);
  ////////////////////////////////////////////////////////////////////////////////////////////////
  //Caption 3////////////////////////////////////////////////////////////////////////////////////
  update_post_meta($post->ID, 'valor_c3', $_POST['valor_c3']);
  if(isset($_POST["custom_element_grid_align_c3"])){
    $meta_element_align_c3 = $_POST['custom_element_grid_align_c3'];
    update_post_meta($post->ID, 'custom_element_grid_align_meta_box_c3', $meta_element_align_c3);
  }
  update_post_meta($post->ID, 'size_c3', $_POST['size_c3']);
  update_post_meta($post->ID, 'color_font_c3', $_POST['color_font_c3']);
  update_post_meta($post->ID, 'color_back_c3', $_POST['color_back_c3']);
  ////////////////////////////////////////////////////////////////////////////////////////////////
  //Image////////////////////////////////////////////////////////////////////////////////////////
  update_post_meta($post_id, '_image_id', $_POST['upload_image_id'] );
  ////////////////////////////////////////////////////////////////////////////////////////////////
  //Configure Link-Target-CButton Color//////////////////////////////////////////////////////////
  if(isset($_POST["custom_parent"])){
	$metaLoopPost = $_POST['custom_parent'];
	update_post_meta($post->ID, 'custom_parent_loop', $metaLoopPost);
  }
  update_post_meta($post->ID, 'link_name', $_POST['link_name']);
  update_post_meta($post->ID, 'link_per', $_POST['link_per']);
  update_post_meta($post->ID, 'color_font_button', $_POST['color_font_button']);
  update_post_meta($post->ID, 'color_top_button', $_POST['color_top_button']);
  update_post_meta($post->ID, 'color_bottom_button', $_POST['color_bottom_button']);
  if(isset($_POST["custom_element_grid_target"])){
    $meta_element_target = $_POST['custom_element_grid_target'];
    update_post_meta($post->ID, 'custom_element_grid_target_meta_box', $meta_element_target);
  }
  update_post_meta($post->ID, 'chance', $_POST['chance']);
}