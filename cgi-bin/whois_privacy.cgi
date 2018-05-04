#!/usr/local/bin/perl

#$Id: whois_privacy.cgi,v 1.3 2006/10/20 23:22:19 sbelikov Exp $
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
	%in %actions $XML_Client %cookies $action
	$authentication $cgi $path_templates $flag_header_sent
	$reg_username $reg_password $reg_domain $cookie $domain_count
	$reg_permission $reg_f_owner $expiredate 
	$waiting_request $domain_info 
	$COOKIE_KEY $affiliate_id $path_to_config
	%unauthenticated_actions
);
( 
	%in, %actions, $XML_Client, %cookies, $action,
	$authentication, $cgi, $path_templates, $flag_header_sent,
    $reg_username, $reg_password, $reg_domain, $cookie, $domain_count,
    $reg_permission, $reg_f_owner, $expiredate, 
    $waiting_request, $domain_info,
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
use warnings;

# initialize global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/whois_privacy";
$COOKIE_KEY = $TEST_SERVER?"REGISTRANT_KEY":"REGISTRANT_LIVE_KEY";
$waiting_request = "";

# allowed actions
%actions = (
	wp_register => \&wp_register,
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

sub wp_register {
	my (%HTML);
	# set initial steps results
	$HTML{affiliate_id} = $affiliate_id;
	$HTML{step1_res} = $HTML{step2_res} = "Not processed";
	
	$reg_domain = $in{reg_domain};
	
	# data to set 
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

		$HTML{step1_res} = "<font color=green>Success!</font>";
		$HTML{step1_expiredate} = $domain_info->{attributes}{ expiredate };

		# step 2: register whois privacy (API: 'sw_register' )
		my $xcp_req = {
		    action => 'sw_register',
		    attributes => {
# Uncomment one of the string or pass a specific value of parameter
# If not passed or value not save|process then settings 
# from RSP profile will be used
#				handle => 'save',  #save order only regardless RSP settings
#				handle => 'process', #process order always regardless RSP settings 
			
				domain => $reg_domain,
				reg_type => 'whois_privacy',
		    },
		};
		
		my $res = $XML_Client->send_cmd( $xcp_req );
		
		$HTML{step2_text} = $res->{ response_text };
		$HTML{step2_success} = $res->{is_success} ? "Successful" : "Fail";
		if (not $res->{is_success}) {
			$HTML{step2_res} = "<font color=red>Failed attempt!</font>";
				
			last PROCESS;
		}
			
		$HTML{step2_res} = "<font color=green>Success!</font>";
		$HTML{step3_text} = "<tr><td nowrap><strong>Step 3) To order to activate Whois Privacy</strong></td><td> You must follow the instructions contained in an email message that has been sent to the Admin Contact address of the domain name.</td></tr>";
	}

    print_form("$path_templates/wp_results.html",\%HTML);
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

	# get domain info
	$domain_info = get_domain_info( $reg_domain, $cookie );
			
	if (not $domain_info->{is_success}) {
		error_out("Failed attempt: $domain_info->{response_text}\n");
		exit;
    }

    # domain used to login with must be one sponsored by this reseller
    if ( not $domain_info->{ attributes }{ sponsoring_rsp } ) {
	error_out( "This domain is not sponsored by this domain provider and cannot be managed from this interface." );
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
	$HTML{reg_type} = "whois_privacy";
    $HTML{orig_domain} = $reg_domain;
    $HTML{idn_link} .= $reg_domain =~ /^xn--/ ? 
	"[<a href=\"$OPENSRS{IDN_CONVERSION_TOOL_LINK}?type=PUNYCODE&input=$reg_domain\" target=\"_blank\">IDN</a>]" : '';
    $HTML{affiliate_id} = $affiliate_id;
    $HTML{expiredate} = $domain_info->{ attributes }{ expiredate };

	print_form("$path_templates/whois_privacy_menu.html",\%HTML,'single');
}

###########################################################################
# print a html header
sub print_header {
    if (not $flag_header_sent) {
        print "Content-Type:  text/html\r\n\r\n";
        $flag_header_sent = 1;
    }
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
            sub_user    => ($in{subuser} and $RENEW{password_send_subuser})
				 ? 1 : 0,
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

