<?php
	require_once('includes/header.php');
?>
  <tr>
    <td  style="height:457px; background:#1E2126">
		<table style="width:766px" class="bg1">
		  <tr>
			<td  style="height:457px;" class="bg2">
				<table style="height:457px">
				  <tr>
					<td  style="width:38px"></td>
					<td  style="width:476px; background:url(http://www.westcoastsoftware.com/images/title_bg.gif) no-repeat; padding-bottom:5px">
					<div style="margin-right:30px; text-align:justify">
						<br style="line-height:24px">
						<img src="http://www.westcoastsoftware.com/images/t1_1.gif" alt=""><br>
						<br style="line-height:10px">
<?php
	require_once 'facebook.php';
	// Copyright 2007 Facebook Corp.  All Rights Reserved. 
	// 
	// Application: WestCoastSoftware
	// File: 'index.php' 
	//   This is a sample skeleton for your application. 
	// 
	$appapikey = '0edafe0b97be8cc27acef665ff00f7e2';
	$appsecret = 'dd69dd1cd09e642226c66ce05ec55fdf';
	$facebook = new Facebook($appapikey, $appsecret);
	$user_id = $facebook->require_login();
	
	// Greet the currently logged-in user!
	echo "<p><font color=\"#FFFFFF\">Hello, <fb:name uid=\"$user_id\" useyou=\"false\" />!</font>&nbsp;&nbsp;&nbsp;<img src=\"https://graph.facebook.com/902020113/picture\"/></p>";
	
	// Print out at most 25 of the logged-in user's friends,
	// using the friends.get API method
	echo "<p>Friends:<br /><br />";
	$friends = $facebook->api_client->friends_get();
	$friends = array_slice($friends, 0, 50);
	echo "<table cellpadding=\"10\">";
	$i = 0;
	foreach ($friends as $friend) {
	  if($i == 0)
	  	echo "<tr><td>";
	  echo "<img src=\"https://graph.facebook.com/$friend/picture\"/><td>&nbsp</td><td>";
	  $i++;
	  if($i == 10)
	  {
	  	echo "</tr></td><tr><td>&nbsp</td></tr>";
	  	$i=0;
	  }
	}
	echo "</table>";
	echo "</p><br />";
?>
<br />
<fb:login-button perms="email,user_birthday"></fb:login-button>
<div id="fb-root"></div>
<script src="http://connect.facebook.net/en_US/all.js"></script>
<script>
  FB.init({appId: '103389623039841', status: true, cookie: true, xfbml: true});
  FB.Event.subscribe('auth.sessionChange', function(response) {
    if (response.session) {
      // A user has logged in, and a new cookie has been saved
    } else {
      // The user has logged out, and the cookie has been cleared
    }
  });
</script>
<br />
<?php
	$user = json_decode(file_get_contents('https://graph.facebook.com/'.$user_id.'?wrap_access_token=' . $cookie['oauth_access_token']))->$user_id;
	echo $user->email . ' ' . $user->name . ' ' . $user->username . ' ' . $user->birthday_date;
	//register_user($user->id, $user->email, $user->name, $user->username,$user->birthday_date);

define('FACEBOOK_APP_ID', 'your application id');
define('FACEBOOK_SECRET', 'your application secret');

function get_facebook_cookie($app_id, $application_secret) {
  $args = array();
  parse_str(trim($_COOKIE['fbs_' . $app_id], '\\"'), $args);
  ksort($args);
  $payload = '';
  foreach ($args as $key => $value) {
    if ($key != 'sig') {
      $payload .= $key . '=' . $value;
    }
  }
  if (md5($payload . $application_secret) != $args['sig']) {
    return null;
  }
  return $args;
}

$cookie = get_facebook_cookie(FACEBOOK_APP_ID, FACEBOOK_SECRET);

?>
<!--                        <br/>
                        
                        <div>
<script src="http://pipes.yahoo.com/js/imagebadge.js">{"pipe_id":"dtSNRhrd3RGRE3f4bLsjiw","_btype":"image"}</script>                        </div>
                        <br/> -->
						<br style="line-height:5px">
						<div style="text-align:right">
<!--							<a href="#"><img src="images/details.gif" alt="" border="0"></a> --><br>  
						</div>
						<br style="line-height:20px">
						<div style="width:auto; background:#353535"><img src="http://www.westcoastsoftware.com/images/spacer.gif" alt="" width="1" height="1"><br></div>	
					</div>	
						<br style="line-height:20px">
						<table style="height:132px; width:446px" class="list">
						  <tr>
							<td  style="width:156px">
								<img src="http://www.westcoastsoftware.com/images/t1_2.gif" alt=""><br>
<!--								<br style="line-height:13px">
								<ul>
								  <li><a href="#">Norton 2007 Products</a></li>
								  <li><a href="#">Free Symantec Toolbar</a></li>
								  <li><a href="#">Remove Virus For Me</a></li>
								  <li><a href="#">Security Response</a></li>
								</ul> -->
							</td>
							<td  style="width:156px">
								<img src="http://www.westcoastsoftware.com/images/t1_3.gif" alt=""><br>
<!--								<br style="line-height:13px">
								<ul>
								  <li><a href="#">Business Products</a></li>
								  <li><a href="#">Windows Protection</a></li>
								  <li><a href="#">Virus Definitions</a></li>
								  <li><a href="#">Removal Tools</a></li>
								</ul> -->
							</td>
							<td  style="width:134px">
								<img src="http://www.westcoastsoftware.com/images/t1_4.gif" alt=""><br>
<!--								<br style="line-height:13px">
								<ul>
								  <li><a href="#">Home Store</a></li>
								  <li><a href="#"> Renewals/Upgrades</a></li>
								  <li><a href="#">New Customer Offers</a></li>
								  <li><a href="#">Small Business Store</a></li>
								</ul> -->
							</td>
						  </tr>
  						  <tr>
							<td colspan="3">&nbsp;</td>
						  </tr>
  						  <tr>
							<td colspan="3">&nbsp;</td>
						  </tr>
						  <tr>
							<td colspan="2">
								<div align="center">
<!--                                    <form method="POST" name="msgform">
										<fieldset>
											<table>
												<tr>
													<td colspan="3">Client Login</td>
												</tr>
												<tr>
													<td colspan="3">&nbsp;</td>
												</tr>
												<tr>
													<td colspan="3">&nbsp;</td>
												</tr>
												<tr>
													<td align="right"><label for="">Username&nbsp;</label></td>
													<td colspan="2"><input class="form-field" type="text" name="email" size="20" tabindex="1"/></td>
												</tr>
												<tr>
													<td colspan="3">&nbsp;</td>
												</tr>
												<tr>
													<td align="right"><label for="">Password&nbsp;</label></td>
													<td colspan="2"><input class="form-field" type="password" name="phone" size="20" tabindex="2"/></td>
												</tr>
												<tr>
													<td colspan="3">&nbsp;</td>
												</tr>
												<tr>
													<td colspan="2">&nbsp;</td><td align="center"><input class="form-button" name="submit" type="submit" value="Login" tabindex="3" onClick="return checkForm();"/></td>
												</tr>
											</table>
										</fieldset>
                                    </form>-->
								</div>
							</td>
							<td>&nbsp;</td>
						  </tr>
						</table>
						<br style="line-height:29px">
						<img src="http://www.westcoastsoftware.com/images/px.gif" alt=""><br>
						<br style="line-height:20px">
                        
<!--						<a href="#"><img src="images/bunner1.jpg" alt="" border="0"></a> --><br> 
					</td>
					<td  style="width:212px">&nbsp;
<!--						<table>
						  <tr>
							<td  style="height:116px; background:url(images/bg1.gif) no-repeat #181A1E" class="list1">
								<div style="margin-left:15px">
									<br style="line-height:18px">
									<img src="images/t1_5.gif" alt=""><br>
									<br style="line-height:9px">
									<ul>
									  <li><a href="#">W32.Lovena.A@mm</a></li>
									  <li><a href="#">Trojan.Tarodrop.B</a></li>
									  <li><a href="#">Microsoft Excel Opcode</a></li>
									</ul> 
								</div>
							</td>
						  </tr>
						  <tr>
							<td  style="height:4px"></td>
						  </tr>
						  <tr>
							<td  style="height:116px; background:url(images/bg2.gif) repeat-x #181A1E" class="list1">
								<div style="margin-left:15px">
									<br style="line-height:18px">
<!--									<img src="images/t1_6.gif" alt=""><br>
									<br style="line-height:9px">
									<ul>
									  <li><a href="#">Spyware.Jgidol</a></li>
									  <li><a href="#">Adware.RaxSearch</a></li>
									  <li><a href="#">Remote Code</a></li>
									</ul> 
								</div>
							</td>
						  </tr>
						  <tr>
							<td  style="height:4px"></td>
						  </tr>
						  <tr>
							<td  style="height:105px; background:url(images/bg2.gif) repeat-x #181A1E" class="list2">
								<div style="margin-left:15px; margin-right:15px">
									<br style="line-height:18px">
<!--									<img src="images/t1_7.gif" alt=""><br>
									<br style="line-height:12px">
									<ul>
									  <li><a href="#">Symantec Authorizes $1 Billion
Share Repurchase Program (Spam
Surge: Storm Trojan)</a></li>
									</ul> 
								</div>
							</td>
						  </tr>
						  <tr>
							<td  style="height:112px; background:url(images/bg2.gif) repeat-x; padding-bottom:5px">
								<br style="line-height:21px">
								<!-- <a href="#"><img src="images/bunner2.jpg" alt="" border="0"></a> <br>
							</td>
						  </tr>
						</table>-->
					</td>
					<td  style="width:40px"></td>
				  </tr>
				</table>
			</td>
		  </tr>
		</table>
	</td>
  </tr>
<?php
	require_once('includes/footer.php');
?>