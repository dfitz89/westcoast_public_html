#!/usr/local/bin/perl

#$Id: renew.cgi,v 1.41 2006/11/22 22:17:27 sbelikov Exp $
# vi: set tabstop=4:
#       .Copyright (C)  1999-2000 TUCOWS.com Inc.
#       .Created:       11/19/2000
#       .Contactid:     <support@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Developed by:  TUCOWS.com Inc. for OpenSRS.com
#       .Written by:    John Jerkovic, Vlad Jebelev
#
#       This program is free software; you can redistribute it and/or
#       modify it under the terms of the GNU Lesser General Public
#       License as published by the Free Software Foundation; either
#       version 2.1 of the License, or (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful, but
#       WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#       Lesser General Public License for more details.
#
#       You should have received a copy of the GNU Lesser General Public
#       License along with this program; if not, write to the Free Software
#       Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

use vars qw(
            %in %contact_types %actions $XML_Client %cookies $action
            $authentication $cgi $path_templates $flag_header_sent
            $reg_username $reg_password $reg_domain $cookie $domain_count
            $reg_permission $reg_f_owner $expiredate $last_access_time
            $last_ip %contact_keys $waiting_request $domain_info 
			$whois_privacy_state
	    $COOKIE_KEY $affiliate_id $path_to_config
	    %unauthenticated_actions
	    );
( %in, %contact_types, %actions, $XML_Client, %cookies, $action,
            $authentication, $cgi, $path_templates, $flag_header_sent,
            $reg_username, $reg_password, $reg_domain, $cookie, $domain_count,
            $reg_permission, $reg_f_owner, $expiredate, $last_access_time,
            $last_ip, %contact_keys, $waiting_request, $domain_info, 
			$whois_privacy_state
  ) = ();


# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
      $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
	  if ($ENV{OSRS_CLIENT_ETC}){
	      $path_to_config = "$ENV{OSRS_CLIENT_ETC}";
	  }
      do "$path_to_config/OpenSRS.conf";
}

use lib $PATH_LIB;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use strict;
use Time::Local;

use CGI ':cgi-lib';
use OpenSRS::XML_Client qw(:default);
use OpenSRS::Util::Common qw(send_email);
use Data::Dumper;

# initialize global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/renew";
$COOKIE_KEY = $TEST_SERVER?"REGISTRANT_KEY":"REGISTRANT_LIVE_KEY";
$waiting_request = "";

# allowed actions
%actions = (
	renew_domain => \&renew_domain,
	send_password => undef,
);

%unauthenticated_actions = (
            send_password   => undef,
);

start_up();

# make a client object we will use to talk to the OpenSRS server
$XML_Client = new OpenSRS::XML_Client(%OPENSRS);
$XML_Client->login;

# read in the form data
ReadParse(\%in);
%cookies = GetCookies();
$action = $in{action};
#-----------------------------------------------------
# perform necessary actions
                                                                                                       
# a few actions are allowed without authentication.
if ( $action and exists $unauthenticated_actions{$action} ) {
    no strict 'refs';
    &$action();
    exit;
}
                                                                                
$affiliate_id = $in{ affiliate_id };

#-----------------------------------------------------
# perform necessary actions
# if they have specified 'login', bypass validate(), and do login()

if ($action eq 'login') { login(); exit }
elsif ($action eq 'logout') {logout(); exit }

# for all other actions, do validate() (grab cookie if it exists)
$authentication = validate();

# show them the login page if they don't have a valid cookie
if (not $authentication) {
    show_login();

# they asked for a valid action
} elsif ($authentication and exists $actions{$action}) {
    &{$actions{ $action }}();

# they gave us an invalid command
} else {
    show_login();
}

# close the connection to the server
$XML_Client->logout;

exit;

####################### START OF SUBS ##############################
sub start_up {
    if ($REGISTER{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
}

sub print_form {
    my ($content);
    my ($template,$HTML) = @_;
    print_header();

    open (FILE, "<$template") or die "Couldn't open $template: $!\n";
    while (<FILE>) {
	s/{{(.*?)}}/$HTML->{$1}/g;
	$content .= $_;
    }
    close FILE;
    print $content;
}

sub error_out {
	my ( $error_msg, $domain ) = @_;

    my (%HTML);
    $HTML{CGI} = $cgi;
    $HTML{ERROR} = $error_msg;
    $HTML{SHOW_PASS} = "";
	
    if ( defined $domain and 
	defined $RENEW{allow_password_requests} and 
	$RENEW{allow_password_requests} ) 
    {
                                                                                
	$domain = $domain;
                                                                                
        if ( $RENEW{password_send_to_admin} ) {
            $HTML{SHOW_PASS} =  qq(Click <a href="$cgi?action=send_password&domain=$domain&user=admin">here</a> to have lost password sent to admin.);
			if ($RENEW{password_send_subuser}){
				$HTML{SHOW_PASS} .=  qq(<br>Click <a href="$cgi?action=send_password&domain=$domain&user=admin&subuser=1">here</a> to have subuser lost password sent to admin.);
			}
        }
        if ( $RENEW{password_send_to_owner} ) {
            $HTML{SHOW_PASS} .= qq(<br>Click <a href="$cgi?action=send_password&domain=$domain&user=owner">here</a> to have lost password sent to owner.);
			if ($RENEW{password_send_subuser}){
				$HTML{SHOW_PASS} .=  qq(<br>Click <a href="$cgi?action=send_password&domain=$domain&user=admin&subuser=1">here</a> to have subuser lost password sent to owner.);
			}
        }
    }
    print_form("$path_templates/error.html",\%HTML);
}

sub get_content {
    my $content;
    my ($template,$HTML) = @_;
    open (FILE, "<$template") or die "Couldn't open $template: $!\n";
    while (<FILE>) {
	s/{{(.*?)}}/$HTML->{$1}/g;
	$content .= $_;
    } 
    close FILE;
    return $content;
}

sub fancy_sort {
    my (@words,@ints);
    my @list = @_;
    foreach (@list) {
	if ($_ =~ /^\d+$/) {
	    push @ints, $_;
	} else {
	    push @words, $_;
	}
    }
    @words = sort @words;
    @ints = sort { $a <=> $b } @ints;
    return (@ints,@words);
}

sub build_select_menu {
    my ($key,$html);
    my $href = shift;
    my $default = shift;
    foreach $key (fancy_sort(keys %$href)) {
		if ($key eq $default) {
			$html .= <<EOF;
<option value="$key" SELECTED> $href->{$key}
EOF
		} else {
			$html .= <<EOF;
<option value="$key"> $href->{$key}
EOF
		}
    }
    return $html;
}

########################################################
sub escape_hash_values {
    my $hash_ref = shift;
    foreach my $hash_key ( keys %$hash_ref ) {
    	if ( ref( $hash_ref->{$hash_key} ) eq "HASH" ) {
		    escape_hash_values( $hash_ref->{$hash_key} );
		} elsif ( ref( $hash_ref->{$hash_key} ) eq "ARRAY" ) {
		    escape_array_values( $hash_ref->{$hash_key} ); }
		else {
    	    $hash_ref->{$hash_key} = escape( $hash_ref->{$hash_key} ); 
		}
    }
}

sub escape_array_values {
    my $array_ref = shift;
    foreach my $array_element ( @$array_ref ) {
    	if ( ref( $array_element ) eq "HASH" ) {
			escape_hash_values( $array_element );
		} elsif ( ref( $array_element ) eq "ARRAY" ) {
			escape_array_values( $array_element );
		} else {
			$array_element = escape( $array_element );	
		}
    }
}

sub escape {
    my $string = shift;
    $string =~ s/\"/&quot;/g;
    return $string;
}

# attempt to validate a user's cookie
sub validate {
    my ($expire,$response);
    $reg_username = "";

    if (exists $cookies{$COOKIE_KEY}) {
		$cookie = $cookies{$COOKIE_KEY};
		my $xcp_request = {
				action => "get",
				object => "userinfo",
				cookie => $cookie,
				};

		$response = $XML_Client->send_cmd( $xcp_request );
		if (not $response->{is_success}) {
			return undef;
		}

		$reg_username = $response->{attributes}->{reg_username};
		$reg_domain = $response->{attributes}->{domain};
		$reg_f_owner = $response->{attributes}->{f_owner};
		$reg_permission = $response->{attributes}->{permission};
		$domain_count = $response->{attributes}->{domain_count};
		$expiredate = $response->{attributes}->{expiredate};
		$waiting_request = $response->{attributes}->{waiting_request};

		return 1;
		
    } else {
		return undef;
    }
}

# get cookies from the client
sub GetCookies {
    my ($cookie, %cookies,$key,$value);
    foreach $cookie (split /\; /, $ENV{HTTP_COOKIE}) {
		($key, $value) = (split /=/, $cookie)[0,1];
		$value =~ s/\\0/\n/g;
		$cookies{$key} = $value;
    }
    return %cookies;
}

# get all info on this domain. Remember: you are only getting info on one
# domain (the one you specified in 'set_cookie' call). If you want info
# on other domains, either switch the cookie to other domains ('update_cookie')
# or get a list of domains ('get_domain' with 'type => list') and use its
# ext_results data
sub get_domain_info {
	my ( $domain_name, $cookie ) = @_;

	my $xcp_req = {
		action => "get",
		object => "domain",
		cookie => $cookie,
		attributes => { type => "all_info" }
    };
		
    return $XML_Client->send_cmd( $xcp_req );
}

sub get_whois_privacy_state {
	my ($domain_name, $cookie) = @_;
	my $xcp_rsp;
	my $xcp_req = {
		action => "get",
		object => "domain",
		cookie => $cookie,
		attributes => {
			type => "whois_privacy_state",
		}
	};
	return $XML_Client->send_cmd( $xcp_req );
}

sub renew_domain {
    my (%HTML);
	my $apply_to_all = "Not processed";

	# set initial steps results
	$HTML{affiliate_id} = $affiliate_id;
	$HTML{step1_res} = $HTML{step2_res} = $HTML{step3_res} = "Not processed";
	
	$reg_domain = $in{reg_domain};
	
	# data to set 
	my $affect_domains = $in{ affect_domains } eq 'on' ? 1 : 0;
	my $period = $in{ renewal_period };
	my $auto_renew = $in{ auto_renew } eq 'on'  ? 1 : 0;
	my $renew_ok = 0;
	$HTML{auto_renew} = $auto_renew;
	$HTML{orig_domain} = $reg_domain;
	$HTML{idn_link} .= $reg_domain =~ /^xn--/ ? 
	    "[<a href=\"$OPENSRS{IDN_CONVERSION_TOOL_LINK}?type=PUNYCODE&input=$reg_domain\" target=\"_blank\">IDN</a>]" : '';
	
	PROCESS: {

		# step 1: get domain info (API: 'get_domain', type: 'all_info' ).
		$domain_info = get_domain_info( $reg_domain, $cookie );
		$HTML{step1_text} = $domain_info->{ response_text };
		if (not $domain_info->{is_success}) {
			$HTML{step1_res} = "<font color=red>Failed attempt!</font>";
			last PROCESS;
		}

		#for .CA use admin contacts because they do not have owner contacts
		if ($reg_domain =~ /\.ca$/){
			$HTML{step1_owner} = $domain_info->{attributes}{contact_set}{admin}{email};
			$HTML{step1_first_name} = $domain_info->{attributes}{contact_set}{admin}{first_name};

		}else{
			$HTML{step1_owner} = $domain_info->{attributes}{contact_set}{owner}{email};
			$HTML{step1_first_name} = $domain_info->{attributes}{contact_set}{owner}{first_name};
		
		}
		$HTML{step1_res} = "<font color=green>Success!</font>";
		$HTML{step1_expiredate} = $domain_info->{attributes}{ expiredate };
		$HTML{step1_auto_renew} = $domain_info->{attributes}{ auto_renew };

		# step 2: renew domain (API: 'renew_domain' )

	    my ($year, undef) = 
			split('-',$domain_info->{ attributes }{ expiredate });

		my $xcp_req = {
		    action => 'renew',
		    object => 'domain',
		    attributes => {
# Uncomment one of the string or pass a specific value of parameter
# If not passed or value not save|process then settings 
# from RSP profile will be used
#			handle => 'save',  #save order only regardless RSP settings
#			handle => 'process', #process order always regardless RSP settings 
			
			domain => $reg_domain,
			currentexpirationyear => $year,
			period => $period,
			auto_renew => $auto_renew,
			affiliate_id => $affiliate_id,
		    },
		};
		
		my $res = $XML_Client->send_cmd( $xcp_req );
		$HTML{step2_text} = $res->{ response_text };
		$HTML{step2_success} = $res->{is_success} ? "Successful" : "Fail";
		if (not $res->{is_success}) {
			if ( $F_QUEUE_SUPPLIER_UNAVAILABLE and 
				 $res->{attributes}{queue_request_id} ){
				$HTML{step2_text} = "Renewal Request has been placed in a registrar's queue";
				$HTML{step2_success} = "Queued";
				$renew_ok = 1;
				#last or next is up to RSP and his customization
				if (not $RENEW{PROCESS_LIST_IF_QUEUED}){
					last PROCESS;	
				}	
			} else {
				$HTML{step2_res} = "<font color=red>Failed attempt!</font>";
				$HTML{step2_auto_renew} = $HTML{step1_auto_renew};
				$HTML{step2_expiredate} = $HTML{step1_expiredate};
				last PROCESS;
			}
			
		} else {
			$renew_ok = 1;
		}

		$HTML{step2_res} = "<font color=green>Success!</font>";
		$HTML{step2_auto_renew} = $res->{attributes}{ auto_renew };
		$HTML{step2_order_id} = $res->{attributes}{ order_id };

		# get new expiration year from the result
		$HTML{step2_expiredate} = 
			$res->{ attributes }{ 'registration expiration date' };

		# step 3: apply auto_renew to all domains in the profile - 
		# only if 'affected_domains' checkbox was checked
		# ( API: 'modify_domain', with data: 'auto_renew' )
		if ( not $affect_domains ) {
			$HTML{step3_res} = $apply_to_all = "Not requested by user";
			last PROCESS;
		}

		$xcp_req = {
			action => "modify",
			object => "domain",
			cookie => $cookie,
			attributes => {
				data => "expire_action",
				auto_renew => $auto_renew,
				let_expire => 0,
				affect_domains => 1,
			}
		};

		$res = $XML_Client->send_cmd( $xcp_req );
		$HTML{step3_text} = $res->{ response_text };
		if (not $res->{is_success}) {
			$apply_to_all = "Failed: $res->{response_text}";
			$HTML{step3_res} = "<font color=red>Fail!</font>";
			last PROCESS;
		}

		$apply_to_all = "Successfully Set";
		$HTML{step3_res} = "<font color=green>Success!</font>";

		# modify_domain doesn't echo info back, so rely on 'is_success' attr
		$HTML{step3_auto_renew} = $auto_renew;
	}

    send_email (
	    "$path_templates/renew.txt",
	    {
			domain		=> $reg_domain,
			success		=> $HTML{step2_success},
			message		=> $HTML{step2_text},
			mailfrom	=> $HTML{step1_owner},
			mailto		=> $RENEW_EMAIL,
			old_expiry	=> $HTML{step1_expiredate},
			old_auto_renew	=> $HTML{step1_auto_renew},
			new_expiry	=> $HTML{step2_expiredate},
			new_auto_renew	=> $HTML{step2_auto_renew},
			apply_to_all	=> $apply_to_all,
			affiliate_id	=> $affiliate_id,
			order_id	=> $HTML{step2_order_id},
	    },
    ) if $RENEW{F_SEND_EMAIL};

	send_email (
		"$path_templates/thankyou.txt",
		{
			mailfrom	=> $RENEW_EMAIL,
			mailto		=> $HTML{step1_owner},
			domain		=> $reg_domain,
			first_name	=> $HTML{step1_first_name},
			num_years	=> $period,
			order_id	=> $HTML{step2_order_id},
			affiliate_id=> $affiliate_id,
		},
	) if $RENEW{F_SEND_EU_EMAIL} and $renew_ok;

    print_form("$path_templates/renewal_results.html",\%HTML);
}

# authenticate user

sub login {
    my $message = shift;

    $reg_username = $in{reg_username};
    $reg_password = $in{reg_password};
	$in{reg_domain} =~ s/^\s+//;
	$in{reg_domain} =~ s/\s+$//;
    $reg_domain = $in{reg_domain};

    if ( not $in{reg_domain} ) {
		error_out("Please enter a domain name.");
		exit;
    } 
    if ( $in{reg_domain} =~ /\s/ ) {
        error_out("Spaces not allowed inside domain name [$in{reg_domain}].");
        exit;
    }



    if ( $in{reg_domain} =~ /[^A-Za-z0-9\.\-]/ ) {
		error_out(
	    "It seems that $in{reg_domain} is an IDN domain.<br>".
	    " Please <a href=\"$OPENSRS{IDN_CONVERSION_TOOL_LINK}?type=NATIVE&input=$in{reg_domain}\" target=\"_blank\">convert".
	    "</a> to Punycode first"
		);
		exit;
    }
    
    if ( not is_capable( $reg_domain )) {
		error_out("
Renew functionality is not currently enabled for $reg_domain.<P>
Please contact your Registration Services Provider for further assistance.");
		exit;
    }

    # get permissions for a given user
    my $xcp_request = {
                action => "set",
                object => "cookie",
                attributes => {
                    domain => $reg_domain,
                    reg_username => $reg_username,
                    reg_password => $reg_password,
		}
    };

    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
        my $error;
        if ( $response->{response_code} == 415 ) {    # bad un/pw
                                                                               
            $error = "Error: Invalid username/password combination for $reg_domain.<br><br>";
                                                                               
            $response->{response_text} =~ s/\n/<br>\n/g;
            $error .= $response->{response_text};
                                                                               
            error_out( $error, $reg_domain );
            exit;
                                                                               
        } else {                                    # any other error
            $error = "$response->{response_text}<br>Please contact Support for
assistance.";
                                                                               
            error_out( $error );
            exit;
        }
    }
 
    $cookie = $response->{attributes}->{cookie};
    $expiredate = $response->{attributes}->{expiredate};

    if (not $cookie) {
        error_out("Invalid username/password given.<br>\n");
        exit;
    }

    my $path = "";
    print "Content-type:  text/html\r\n";
    print "Set-Cookie: $COOKIE_KEY=$cookie; PATH=$path\r\n";
    print "\r\n";
    $flag_header_sent = 1;
	
	# get whois_privacy_state
	my $whois_privacy = get_whois_privacy_state($reg_domain, $cookie);
	$whois_privacy_state =
            ($whois_privacy->{attributes}->{state} eq "enabled") ? "Yes" : "No";

	# get domain info
	$domain_info = get_domain_info( $reg_domain, $cookie );
			
	if (not $domain_info->{is_success}) {
		error_out("Failed attempt: $domain_info->{response_text}\n");
		exit;
    }

    # domain used to login with must be one sponsored by this reseller
    if ( not $domain_info->{ attributes }{ sponsoring_rsp } ) {
	error_out( "This domain is not sponsored by this domain provider, and cannot be renewed/autorenewed from this interface." );
	exit;
    }

    main_menu($cgi);
}

#############################################################################
# logout user (delete cookie)
sub logout {
    my ($cookie, $response);
    if (exists($cookies{$COOKIE_KEY})) {
        $cookie = $cookies{$COOKIE_KEY};
        my $xcp_request = {
                    action => "delete",
                    object => "cookie",
                    cookie => $cookie,
                    attributes => {
                        cookie => $cookie,
		    }
		};
	 $response = $XML_Client->send_cmd( $xcp_request );
    }
    show_login();
}

sub show_login {
	my $message = shift;
	
	my (%HTML);
	$HTML{MESSAGE} = $message;

    $HTML{CGI} = $cgi;
	$HTML{affiliate_id} = $affiliate_id;
    
	if ( defined $message and $message ) {
        $HTML{MESSAGE} = qq(<font color="red">$message</font><br><br>);
    }

	print_form("$path_templates/login.html",\%HTML,'single');
}

sub main_menu {
    my (%HTML);
    
	$HTML{CGI} = $cgi;
    $HTML{reg_domain} = $reg_domain;
    $HTML{orig_domain} = $reg_domain;
    $HTML{idn_link} .= $reg_domain =~ /^xn--/ ? 
	"[<a href=\"$OPENSRS{IDN_CONVERSION_TOOL_LINK}?type=PUNYCODE&input=$reg_domain\" target=\"_blank\">IDN</a>]" : '';
    $HTML{affiliate_id} = $affiliate_id;
    $HTML{expiredate} = $domain_info->{ attributes }{ expiredate };
    $HTML{auto_renew} = $domain_info->{ attributes }{ auto_renew } ?
	'CHECKED' : '';
	$HTML{whois_privacy_state} = $whois_privacy_state;
    my ( $tld ) = $reg_domain =~ m/$OPENSRS_TLDS_REGEX$/i;

    if ($tld eq '.name') {
	$HTML{forwarding_email} = $domain_info->{ attributes }{ forwarding_email } 
	      ? $domain_info->{ attributes }{ forwarding_email } : 'n/a';	
    	print_form("$path_templates/renew_domain_menu_name.html",\%HTML,'single');

    } else {
	print_form("$path_templates/renew_domain_menu.html",\%HTML,'single');
    }
}

###########################################################################
# print a html header
sub print_header {
    if (not $flag_header_sent) {
        print "Content-Type:  text/html\r\n\r\n";
        $flag_header_sent = 1;
    }
}

# function to check whether a given operation applies to a domain
sub is_capable {
	my ( $domain_name ) = @_;
	my $is_it;

	my $caps = $RENEW{capability};
	foreach my $tld ( keys %$caps ) {
		next unless $caps->{ $tld };
		if ( $domain_name =~ /$tld$/i ) {
			$is_it = 1;
			last;
		}
	}
	return $is_it;
}

sub send_password {
    if ( not exists $RENEW{allow_password_requests} or
            not $RENEW{allow_password_requests} ) {
        show_login("Invalid action: $action");
        exit;
    }
                                                                                
    my $domain = $in{domain};
    $domain =~ s/^\s+|\s+$//g;
    if ( not $domain ) {
        error_out( "No domain specified");
        exit;
    }
	
	my $xcp_request = {
        action      => 'send_password',
        object      => 'domain',
        attributes  => {
            domain_name => $domain,
            send_to     => $in{user},
            sub_user    => ($in{subuser} and $RENEW{password_send_subuser})                                 ? 1 : 0,
        }
    };
    my $response = $XML_Client->send_cmd( $xcp_request );
    
	if ( $response->{is_success} ) {
        show_login( "Password has been sent." );
    } else {
        error_out("Couldn't send password: $response->{response_text}\n");
        exit;
    }
}

