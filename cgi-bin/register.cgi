#!/usr/local/bin/perl

#       .Copyright (C)  1999-2000 TUCOWS.com Inc.
#       .Created:       11/19/1999
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Originally Developed by:
#                       VPOP Technologies, Inc. for Tucows/OpenSRS
#       .Authors:       Joe McDonald, Tom McDonald, Matt Reimer, Brad Hilton,
#                       Daniel Manley
#
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
	    %in $cgi $path_templates $XML_Client %actions $action
	   );
( %in, $cgi, $path_templates, $XML_Client, %actions, $action ) = ();

# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
    $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
    if ($ENV{OSRS_CLIENT_ETC}){
        $path_to_config = "$ENV{OSRS_CLIENT_ETC}";
    } 
    do "$path_to_config/OpenSRS.conf"; 
}

use CGI ':cgi-lib';
use strict;
use lib $PATH_LIB;

$path_templates = "$PATH_TEMPLATES/register";
$cgi = $ENV{SCRIPT_NAME};


# Do not make this script publicly accessible if you
# are not sure what you are doing.
#
# This script will by-pass any settings to pend orders.
# 
if ( not $SHOW_REGISTER ) {
    print "Content-type:  text/html\n\n";
    error_out("This script is disabled via the  flag
within the OpenSRS.conf file. Please keep in mind that
this script will by-pass your \"pend orders\" setting as
set in the RWI. "); 
    exit;
}

use OpenSRS::XML_Client qw(:default);
use OpenSRS::Util::Common qw/locale_build_country_list/;

# global defines
%in = ();

# allowed actions
%actions = (
	    register => undef,
	    register_new => undef,
	    do_register => undef,
	    get_userinfo => undef,
	   );

print "Content-type:  text/html\n\n";

# set the debugging level
start_up();

# make a client object we will use to talk to the OpenSRS server
$XML_Client = new OpenSRS::XML_Client(%OPENSRS);
$XML_Client->login;

# read in the form data
ReadParse(\%in);

$action = $in{action};

# no action was passed so use the default
if (not $action) {
    main_menu();

# they passed a valid action
} elsif (exists $actions{$action}) {
    no strict "refs";
    &$action();
    use strict;

# they passed an invalid action
} else {
    main_menu("Invalid action: $action");
}

# close the connection to the server
$XML_Client->logout;

exit;

sub start_up {

    if ($REGISTER{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
}

##########################################################################
sub print_form {

    my ($content);
    my ($template,$HTML) = @_;

    open (FILE, "<$template") or die "Couldn't open $template: $!\n";
    while (<FILE>) {
	s/{{(.*?)}}/$HTML->{$1}/g;
	$content .= $_;
    }
    close FILE;
    print $content;
}

sub error_out {
    
    my (%HTML);
    $HTML{CGI} = $cgi;
    $HTML{ERROR} = shift;
    print_form("$path_templates/error.html",\%HTML);
    
}

####################################################
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

######################################################
##
sub main_menu {

    my (%HTML);
    $HTML{CGI} = $cgi;
    print_form("$path_templates/main_menu.html",\%HTML);
}

sub register_new {

    my (%HTML);
    $HTML{CGI} = $cgi;

    $HTML{PERIOD_LIST} = build_select_menu(\%REG_PERIODS,1);

    $HTML{ADMIN_COUNTRY_LIST} = locale_build_country_list();
    $HTML{BILLING_COUNTRY_LIST} = $HTML{ADMIN_COUNTRY_LIST};
    $HTML{TECH_COUNTRY_LIST} = $HTML{ADMIN_COUNTRY_LIST};
    $HTML{OWNER_COUNTRY_LIST} = $HTML{ADMIN_COUNTRY_LIST};
    
    print_form("$path_templates/register_new.html",\%HTML);

}

sub do_register {

    my (%HTML,$error,$field,$xcp_request);

    my $form_data = {%in};

    my $f_new_profile = $in{f_new_profile};
    my $reg_username = $in{reg_username};
    my $reg_password = $in{reg_password};
    my $reg_password2 = $in{reg_password2};

    if ($f_new_profile) {
	if ($reg_password ne $reg_password2) {
	    error_out("Password mismatch.<br>\n");
	    exit;
	}
    }

    my @contact_fields = qw( first_name last_name org_name address1 address2
                             address3 city state postal_code country phone fax
                             email url );

    # if they chose these flags, assign the admin contact data to the others
    my $billing_same_as_admin = $in{billing_same_as_admin};
    my $tech_same_as_admin = $in{tech_same_as_admin};

    foreach $field (@contact_fields) {
	$form_data->{contact_set}->{owner}->{$field} = $form_data->{"owner_$field"};
	delete $form_data->{"owner_$field"};
	$form_data->{contact_set}->{admin}->{$field} = $form_data->{"admin_$field"};
	delete $form_data->{"admin_$field"};
	$form_data->{contact_set}->{billing}->{$field} = $form_data->{"billing_$field"};
	delete $form_data->{"billing_$field"};
	$form_data->{contact_set}->{tech}->{$field} = $form_data->{"tech_$field"};
	delete $form_data->{"tech_$field"};
    }
    
    # assign the admin data to billing
    if ($billing_same_as_admin) {
	$form_data->{contact_set}->{billing} = $form_data->{contact_set}->{admin}
    }
    # assign the admin data to tech
    if ($tech_same_as_admin) {
	$form_data->{contact_set}->{tech} = $form_data->{contact_set}->{admin}
    }

    $form_data->{nameserver_list} = [];
    my $sortorder = 1;
    foreach my $fqdn ( grep /^fqdn\d+$/, sort keys %{$form_data} )
    {
    	my $name = $form_data->{$fqdn};
	if ( defined $name )
	{
	    push @{$form_data->{nameserver_list}},
	    	    { name => $name, sortorder => $sortorder };
	    delete $form_data->{$fqdn};
	    $sortorder++;
	}
    }
   
    $form_data->{custom_nameservers} = '';
    
    $xcp_request = {
    	    	action => "register",
		object => "domain",
		attributes => $form_data,
		};
		
    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
	$error = "Failed registration: $response->{response_text}.<br>\n";
	if ($response->{attributes}->{error}) {
	    $response->{attributes}->{error} =~ s/\n/<br>\n/g;
	    $error .= $response->{attributes}->{error};
	}
	error_out($error);
	exit;
    }

    $HTML{MESSAGE} = "Domain $in{domain} successfully registered.<br>\n";
    print_form("$path_templates/do_register.html",\%HTML);
}

sub get_userinfo {

    my $reg_username = $in{username};
    my $reg_password = $in{password};
    my $reg_domain = $in{domain};
	my %HTML;

    my $xcp_request = {
		    action => "get",
		    object => "domain",
		    attributes => {
			type => "all_info",
			reg_username => $reg_username,
			reg_password => $reg_password,
			domain => $reg_domain,
		    }
		   };

    my $response = $XML_Client->send_cmd( $xcp_request );
    if (not $response->{is_success}) {
	error_out("Failed attempt: $response->{response_text}");
	exit;
    }

    # process this through escape() to account for " and ' in the data
    escape_hash_values( $response );

    #
    # now have to convert object format into denormalized format
    #
    foreach my $typeKey ( keys %{$response->{attributes}->{contact_set}} ) {
	foreach my $dataKey ( keys %{$response->{attributes}->{contact_set}->{$typeKey}} ) {
	    $HTML{$typeKey."_".$dataKey} =
	    	$response->{attributes}->{contact_set}->{$typeKey}->{$dataKey};
	}
    }
    
    delete $response->{attributes}->{contact_set};

    my $fqdnCounter = 1;
    foreach my $nameserver ( @{$response->{attributes}->{nameserver_list}} ) {
	$HTML{"fqdn".$fqdnCounter} = $nameserver->{name};
	$fqdnCounter++;
    }
    delete $response->{attributes}->{nameserver_list};
    
    foreach my $attrKey ( keys %{$response->{attributes}} ) {
	$HTML{$attrKey} = $response->{attributes}->{$attrKey};
    }

    $HTML{CGI} = $cgi;
    $HTML{reg_username} = $reg_username;
    $HTML{reg_password} = $reg_password;
    $HTML{reg_domain} = $reg_domain;

    $HTML{PERIOD_LIST} = build_select_menu(\%REG_PERIODS,1);
    
    $HTML{OWNER_COUNTRY_LIST} = locale_build_country_list($HTML{owner_country});
    $HTML{ADMIN_COUNTRY_LIST} = locale_build_country_list($HTML{admin_country});
    $HTML{BILLING_COUNTRY_LIST} = locale_build_country_list($HTML{billing_country});
    $HTML{TECH_COUNTRY_LIST} = locale_build_country_list($HTML{tech_country});
    print_form("$path_templates/register.html",\%HTML);
    
}

