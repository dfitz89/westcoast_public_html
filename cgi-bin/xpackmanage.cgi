#!/usr/local/bin/perl
                                                                                    
#       .Copyright (C)  1999-2000 TUCOWS.com Inc.
#       .Created:       11/19/1999
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Originally Developed by:
#                       VPOP Technologies, Inc. for Tucows/OpenSRS
#       .Authors:       Joe McDonald, Tom McDonald, Matt Reimer, Brad Hilton,
#                       Daniel Manley, Gennady Krizhevsky, John Jerkovic,
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


# global defines
use vars qw(
    %in %contact_types %actions $XML_Client %cookies $action
    $authentication $cgi $path_templates $flag_header_sent
    $reg_username $reg_password $reg_domain $cookie $domain_count 
    $expiredate $waiting_xpack_requests_no $last_access_time $last_ip %contact_keys 
    $COOKIE_KEY $T_EXPIRED $T_EXPIRING $t_mode $notice_days 
    %unauthenticated_actions
);
(
    %in, %contact_types, %actions, $XML_Client, %cookies, $action, 
    $authentication, $cgi, $path_templates, $flag_header_sent,
    $reg_username, $reg_password, $reg_domain, $cookie, $domain_count, 
    $expiredate, $waiting_xpack_requests_no, $last_access_time, 
    $last_ip, %contact_keys  
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
use CGI ':cgi-lib';
use strict;

use Time::Local;
use HTML::Template;
use OpenSRS::XML_Client;
use OpenSRS::Util::Common qw(locale_build_country_list);

# initialize global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/xpackmanage";
local $ENV{HTML_TEMPLATE_ROOT} = "$PATH_TEMPLATES/xpackmanage";
$COOKIE_KEY = $TEST_SERVER?"REGISTRANT_KEY":"REGISTRANT_LIVE_KEY";
$flag_header_sent = 0;	# whether html header has been sent
%in = ();
$reg_username = "";
$reg_password = "";

$reg_domain = "";
$cookie = "";
$domain_count = undef;
$expiredate = undef;
$last_access_time = undef;
$last_ip = undef;
$waiting_xpack_requests_no =undef;

$T_EXPIRING = 1; # there are domains to expire in $notice_days days
$T_EXPIRED  = 2; # there are expired domains
$t_mode = undef; # can be 0, $T_EXPIRING, $T_EXPIRED or ($T_EXPIRING | $T_EXPIRED)
$notice_days  = $MANAGE{ notice_days } ? $MANAGE{ notice_days } : 60;
# list of contact types
%contact_types = (
		  owner => 'Organization',
		  admin => 'Admin',
		  billing => 'Billing',
		  tech => 'Technical',
		 );

%contact_keys = (
    	    	 first_name => undef,
    	    	 last_name => undef,
    	    	 address1 => undef,
    	    	 address2 => undef,
    	    	 address3 => undef,
    	    	 city => undef,
    	    	 state => undef,
    	    	 postal_code => undef,
    	    	 country => undef,
    	    	 email => undef,
    	    	 url => undef,
    	    	 fax => undef,
    	    	 phone => undef,
    	    	 org_name => undef,
    	    	);

# secure actions; require valid cookie
%actions = (
	    get_all_info => undef,
	    update_all_info => undef,
	    show_login => undef,
	    view_waiting_history => undef,
	   );
%unauthenticated_actions = (
	    login	    => undef,
	    logout	    => undef,
	    send_password   => undef,
	    
);

# start things up
start_up();

# create a client object 
$XML_Client = new OpenSRS::XML_Client(%OPENSRS);
$XML_Client->login;

# read in the form data
ReadParse(\%in);
%cookies = GetCookies();
$action = $in{action};

##$action ||= 'show_login';
#-----------------------------------------------------
# perform necessary action
if ( $action and exists $unauthenticated_actions{$action} ) {

    no strict 'refs';
    &$action();
    exit;
}
# for all other actions, do validate() (grab cookie if it exists)
# if validate() fails, send them to the low-access menu
$authentication = validate();
################################################
### At this point, the following variables will be set if they logged in:
### $user_object,$user_id,$profile,$post_permission
# show them the login page if they don't have a valid cookie

if (not $authentication) {
    show_login();
# no action was passed but they have a valid cookie
} elsif (not $action) {
    get_all_info();
# they asked for a valid action
} elsif (exists $actions{$action} ) {
    no strict "refs";
    &$action();
    use strict;
# they gave us an invalid command
} else {
    get_all_info("Invalid action: $action");
}

$XML_Client->logout;

exit;

sub start_up {

    if ($MANAGE{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
    
}

# show login page for non-secure users
sub show_login {
    my $message = shift;
    my %HTML = ();
    $HTML{message} = $message;
    $HTML{MANAGE_WEBDIR} = $MANAGE_WEBDIR;
    print_html_form(template => "$path_templates/login.html", data => \%HTML);
}


sub get_all_info {

    my ($error);
    my $message =shift;
    
    my $type = $in{type};
    my $read_only =$in{read_only};
    if (not defined $read_only){
	$read_only = 1;
    }
    
    my $xcp_request = {
                   action => "get",
                   object => "domain",
                   cookie => $cookie,
		   attributes => {
			type => 'all_info',
		   }
                   };
    
    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
	$error = "Failed attempt: $response->{response_text}<br>\n";
	error_out($error);
	exit;
    }
    # process this through escape() to account for " and ' in the data
    escape_hash_values( $response );
    my %HTML = ();

    $HTML{MANAGE_WEBDIR} = $MANAGE_WEBDIR;
    #print all contacts and NSs
    foreach my $field (qw/ first_name last_name org_name address1 address2 address3 city state country state postal_code phone fax email/){
	$HTML{"owner_$field"}  = $response->{attributes}{contact_set}{owner}{$field} ;
	$HTML{"admin_$field"}  = $response->{attributes}{contact_set}{admin}{$field} ;
	$HTML{"billing_$field"}  = $response->{attributes}{contact_set}{billing}{$field} ;
	$HTML{"tech_$field"}  = $response->{attributes}{contact_set}{tech}{$field} ;
	
    }
    my $fqdnCounter = 1;
    foreach my $nameserver ( @{$response->{attributes}{nameserver_list}}) {
	$HTML{"fqdn$fqdnCounter"} = $nameserver->{name} ;
	$HTML{"ipaddress$fqdnCounter"} = $nameserver->{ipaddress} ;
	$fqdnCounter++;
    }    
    if ($last_access_time) {
	my $human_time = scalar localtime($last_access_time);
	$HTML{last_access} = "<br>Last login: $human_time";
	    if ($last_ip) {
		$HTML{last_access} .= " from $last_ip";
	    }
    }
    $HTML{convert_link} = "[<a href=\"$OPENSRS{IDN_CONVERSION_TOOL_LINK}?type=PUNYCODE&input=$reg_domain\" target=\"_blank\">IDN</a>]"
    if $reg_domain =~ /^xn--/;
			
    $HTML{reg_username} = $reg_username;			    
    $HTML{contact_type} = $contact_types{$type};
    $HTML{domain_name} = $reg_domain;
    $HTML{cgi} = $cgi;
    $HTML{owner_country_list} = locale_build_country_list($HTML{owner_country});
    $HTML{billing_country_list} =locale_build_country_list($HTML{billing_country});
    $HTML{admin_country_list} = locale_build_country_list($HTML{admin_country});
    $HTML{tech_country_list} = locale_build_country_list($HTML{tech_country});
    $HTML{read_only} = $read_only;	    
    $HTML{message} = $message;
    $HTML{expiredate} = $response->{attributes}{expiredate};
    $HTML{waiting_xpack_requests_no} = $waiting_xpack_requests_no;

    print_html_form( template => "$path_templates/get_all_info.html", data => \%HTML);
}

# process data to modify contact info
sub update_all_info {
    
    my ($key, $error, $type);
    if ($in{submit} =~ /cancel/i) {
	get_all_info("Changes cancelled");
	exit;
    }

    my $xcp_request = {
		action => "update_all_info",
		object => "domain",
		cookie => $cookie,
		attributes => {
		    contact_set => {},
		    nameserver_list => [ ],
		    }
		};

    foreach $key ( sort keys %in) {
	if ( $key =~ /^(owner|billing|tech|admin)_/i ) {
	    my $contact_type = $1;
	    my $contact_key = $key;
	    $contact_key =~ s/^(owner|billing|tech|admin)_//i;
	    if  ( exists $contact_keys{$contact_key} ) {
		#strip white spaces
		$in{$key} =~ s/(^\s+)|(\s+$)//g;
		$xcp_request->{attributes}->{contact_set}->{$contact_type}->{$contact_key} = $in{$key};
	    }
	    next;
	}
        # Push the name servers list.
	if ( $key =~ /^fqdn(\d)+$/i ) {
	    if ($in{$key} ){
		push @{$xcp_request->{attributes}->{nameserver_list}},
		{ fqdn => $in{$key}, ipaddress => $in{"ipaddress$1"} };
	    }
	    next;
	}
			
    }#foreach	

    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
	if ( not keys %{$response->{attributes}{details}} ) { 
            $error .= "Failed attempt: $response->{response_text}.<br>\n";
	    if ($response->{attributes}{error}) {
	        $response->{attributes}{error} =~ s/\n/<br>\n/g;
	        $error .= $response->{attributes}{error};
	    }
	    error_out($error);
	    exit;
        }
    }
    
    $waiting_xpack_requests_no = $response->{attributes}{waiting_requests_no};	
    my $resultString = $response->{response_text} ." The request will be reviewed.";
    get_all_info($resultString);
}

# print a html header
sub print_header {
    if (not $flag_header_sent) {
	print "Content-type:  text/html\n\n";
	$flag_header_sent = 1;
    } 
}
									      
# handy method to show default error page
sub error_out {
    my ( $error_msg, $domain ) = @_;
    my (%HTML);

    $HTML{CGI} = $cgi;
    $HTML{ERROR} = $error_msg;
    $HTML{SHOW_PASS} = "";
    
    if ( defined $domain and defined $MANAGE{allow_password_requests} and $MANAGE{allow_password_requests} ) {
    
        if ( $MANAGE{password_send_to_admin} ) {
	    $HTML{SHOW_PASS} =  qq(Click <a href="$cgi?action=send_password&domain=$domain&user=admin">here</a> to have lost password sent to admin.);
	    if ($MANAGE{password_send_subuser}){
		$HTML{SHOW_PASS} .=  qq(Click <a href="$cgi?action=send_password&domain=$domain&user=admin&subuser=1">here</a> to have subuser lost password sent to admin.);
	    }
	} 
	if ( $MANAGE{password_send_to_owner} ) {
	    $HTML{SHOW_PASS} .= qq(<br>Click <a href="$cgi?action=send_password&domain=$domain&user=owner">here</a> to have lost password sent to owner.);
	    if ($MANAGE{password_send_subuser}){
		$HTML{SHOW_PASS} .=  qq(Click <a href="$cgi?action=send_password&domain=$domain&user=owner&subuser=1">here</a> to have subuser lost password sent to owner.);
	    }
	}
    }

    print_html_form(template => "$path_templates/error.html",data =>\%HTML);
}

sub escape_hash_values {

    my $hash_ref = shift;
    foreach my $hash_key ( keys %$hash_ref )
    {
    	if ( ref( $hash_ref->{$hash_key} ) eq "HASH" )
	{
	    escape_hash_values( $hash_ref->{$hash_key} );
	}
    	elsif ( ref( $hash_ref->{$hash_key} ) eq "ARRAY" )
	{
	    escape_array_values( $hash_ref->{$hash_key} );
	}
	else
	{
    	    $hash_ref->{$hash_key} = escape( $hash_ref->{$hash_key} );
	}
    }
}

sub escape_array_values {

    my $array_ref = shift;
    foreach my $array_element ( @$array_ref )
    {
    	if ( ref( $array_element ) eq "HASH" )
	{
	    escape_hash_values( $array_element );
	}
    	elsif ( ref( $array_element ) eq "ARRAY" )
	{
	    escape_array_values( $array_element );
	}
	else
	{
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
	$reg_username = $response->{attributes}->{username};
	$reg_domain = $response->{attributes}->{domain};
	$domain_count = $response->{attributes}->{domain_count};
	$expiredate = $response->{attributes}->{expiredate};
	$waiting_xpack_requests_no = $response->{attributes}->{waiting_requests_no};

	return 1;
	
    } else {
	return undef;
    }
    
}

# get cookies from the client
sub GetCookies {

    my ($cookie, %cookies,$key,$value);

    foreach $cookie (split /\; /, $ENV{HTTP_COOKIE})	{
	($key, $value) = (split /=/, $cookie)[0,1];
	$value =~ s/\\0/\n/g;
	$cookies{$key} = $value;
    }
    return %cookies;
}

#####################################################################
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
    
    if ( $in{reg_domain} =~ /^www\..*$OPENSRS{OPENSRS_TLDS_REGEX}$/i   ) {
        error_out("Please, do not put www. as part of your domain name");
        exit;
    }
 
    my ($tld) = $reg_domain =~ /$OPENSRS{OPENSRS_TLDS_REGEX}$/;
    if ( exists $CANT_SUPPORT{$tld} ) {
    	my $message = <<EOF;
You cannot currently make changes to $tld domains through this<BR>
interface. We will have a $tld enabled Manage Domain interface in place as<BR>
soon as possible.</P>
If need to make emergency nameserver changes to your domain, please contact
<a href="mailto:support\@opensrs.org">support\@opensrs.org</a>.
EOF
    	error_out($message);
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
	
	} else {				    # any other error
	    $error = "$response->{response_text}<br>Please contact Support for assistance.";
	    
	    error_out( $error );
	    exit;
	}
    }
    
    if ( $response->{redirect_url} ) {
	print "Location: ".$response->{redirect_url}."\n\n";
    }
    
    $domain_count = $response->{attributes}->{domain_count};
    $expiredate = $response->{attributes}->{expiredate};
    $last_access_time = $response->{attributes}->{last_access_time};
    $last_ip = $response->{attributes}->{last_ip};
    $waiting_xpack_requests_no = $response->{attributes}->{waiting_requests_no};
    $cookie = $response->{attributes}->{cookie};
    $cookies{$COOKIE_KEY} = $cookie;
    validate();
    my $path = "";
    print "Content-type:  text/html\n";
    print "Set-Cookie: $COOKIE_KEY=$cookie; PATH=$path\n";
    print "\n";
    $flag_header_sent = 1;

    get_all_info($message);
}

#############################################################################
# logout user (delete cookie)
sub logout {
    
    my ($cookie);
    
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

	$XML_Client->send_cmd( $xcp_request );

    }
    
    show_login();
}

sub get_select_content {
    my $sel_opt = shift;
    my $hashptr = shift;  
    my $htmldata = "";
    foreach my $item (sort {$a<=>$b} keys %$hashptr){
	if ($item eq $sel_opt){
	    $htmldata .= "<option value=\"$item\" SELECTED> $$hashptr{$item}\n";	    
	}
	else{
	    $htmldata .= "<option value=\"$item\"> $$hashptr{$item}\n";	    
	}
    }
    return $htmldata;
}


sub send_password {
    if ( not exists $MANAGE{allow_password_requests} or
	    not $MANAGE{allow_password_requests} ) {
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
	action	    => 'send_password',
	object	    => 'domain',
	attributes  => {
	    domain_name	=> $domain,
	    send_to	=> $in{user},
            sub_user    => ($in{subuser} and $MANAGE{password_send_subuser})                                 ? 1 : 0,
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

# display waiting request history for this domain
sub view_waiting_history {

    my (%HTML,$record);

    my $waiting_actions = {
    	    	    
		    domain_new_registration => "Registration",
		    domain_renewal => "Renew",
		    domain_transfer => "Transfer-In",
		    domain_change => "Change Contacts",
		    domain_revoke => "Revoke",
    	    	    };

    # get domains for a given user
    my $xcp_request = {
    	    	action => "get",
		object => "domain",
		cookie => $cookie,
		attributes => {
		    type => "xpack_waiting_history",
		    }
	    };

    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
	error_out("Failed attempt: $response->{response_text}\n");
	exit;
    }

    my $record_count = $response->{attributes}->{record_count};
    my @records = @{$response->{attributes}->{waiting_history}};

    $HTML{waiting_history} = "";
    if ( not scalar @records )
    {
    	$HTML{waiting_history} .= <<EOF
<TR bgcolor="#e0e0e0">
<TD colspan=5 align=center>No history found</TD>
</TR>
EOF
    }
    else
    {
	foreach $record (@records) {
	    my $w_action = $waiting_actions->{$record->{req_type}};
	    $w_action||=$record->{req_type}; # if undefined or new action

    	    $HTML{waiting_history} .= <<EOF;
<TR bgcolor="#e0e0e0">
    <TD align=center>$record->{xpack_req_id}&nbsp;</TD>
    <TD align=center>$w_action&nbsp;</TD>
    <TD>$record->{create_time}&nbsp;</TD>
    <TD align=center>$record->{current_state}&nbsp;</TD>
</TR>
EOF

	}
    }

    $HTML{cgi} = $cgi;
    $HTML{reg_username} = $reg_username;
    $HTML{domain_name} = $reg_domain;
    $HTML{expiredate} = $expiredate;
    $HTML{waiting_xpack_requests_no} = $waiting_xpack_requests_no;
    
    print_html_form(template => "$path_templates/waiting_history.html", data => \%HTML);
}


# print html header
sub print_html_form {
                                                                               
    my %args = @_;
    $args{title} = $args{title} || 'Manage Your Domain';
    my $template = HTML::Template->new(
        cache => 1,
	filename => $args{template},
	die_on_bad_params => 0,
    );
    $template->param(
	CGI => $cgi,
	%{ $args{data} },
    );
    if (not $args{not_framed}) {
#	my $content = $template->output;
#	$template = HTML::Template->new(
#	    cache => 1,
#	    filename => "$path_templates/get_all_info.html",
#	    die_on_bad_params => 0,
#	);
#	$template->param(CONTENT => $content);
    }
#    $template->param(
#	CGI => $cgi,
#	%{ $args{data} },
#	user_id => $user_id,
#    );
    
    print_header();
    print $template->output;

}

									
