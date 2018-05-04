#!/usr/local/bin/perl
#       .Copyright (C)  2002 TUCOWS.com Inc.
#       .Created:       2002/11/11
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://opensrs.org
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
#       Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#	MA 02111-1307 USA

# $Id: tpp_renew.cgi,v 1.6 2004/01/13 21:29:36 epirogov Exp $

use vars qw(
    %in $cgi $path_templates %actions $action %cc_types $TPP_Client
    %contact_keys %data @cc_types %CERT_CONTACT_FIELDS $COOKIE_NAME %cookies
    $flag_header_sent $user_id
);

# Null these things out for mod_perl users
(%in, $cgi, $path_templates, %actions, $action, %cc_types,
    @cc_types, $TPP_Client, %contact_keys, %data) = ();

# pull in conf file with defined values
BEGIN {
    # first "do" the major config file
    do "<path_to_conf_files>/OpenSRS.conf";

    # now load up the config for Certificate service
    do "<path_to_conf_files>/Renewals.conf";
}

use strict;
use lib $PATH_LIB;
use CGI ':cgi-lib';
use HTML::Template;
use Core::Exception;
use Core::Checksum qw(calculate compare);
use OpenSRS::TPP_Client;
use OpenSRS::ResponseConverter;
use OpenSRS::Util::Common qw(build_select_menu build_select_menu3
			    build_country_list CODE_2_Country);

# global defines
$user_id = undef;
$cgi = $ENV{SCRIPT_NAME};
$COOKIE_NAME = "OPENSRS_TPP_CLIENT";
$flag_header_sent = 0;
$path_templates = "$PATH_TEMPLATES/tpp_renew";
%in = ();

# list of valid actions to execute
%actions = (
    login => undef,
    do_login => undef,
    logout => undef,
    main => undef,
    check_renew => undef,
    renew => undef,
);

# start things up
start_up();

# create a client object which we will use to connect to the Tucows server
$TPP_Client = new OpenSRS::TPP_Client(
    %OPENSRS,
    response_converter => new OpenSRS::ResponseConverter(),
);
$TPP_Client->login;

# read in the form data
ReadParse(\%in);
delete $in{error_message};
%cookies = GetCookies();

$action = $in{action};

# perform necessary action
if (not $action) {
    # if action was supplied, use the defaults
    validate() ? main() : login();
} elsif (exists $actions{$action}) {
    # they passed a valid action
    if (($action eq 'do_login') or validate()) {
	no strict "refs";
	&$action();
	use strict;
    } else {
	login();
    }
} else {
    # they passed an invalid action
    error_out("Invalid action: $action");
}

# close connection to the server
$TPP_Client->logout;

exit;

###########################################################

sub start_up {
    if ($RENEWALS{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
    
    OpenSRS::Util::Common::initialize(
	path_templates => $PATH_TEMPLATES,
	mail_settings => \%MAIL_SETTINGS
    );
}

# get cookies from the client
sub GetCookies {
    my %cookies = ();
    foreach my $cookie (split /\; /, $ENV{HTTP_COOKIE}) {
	my ($key, $value) = (split /=/, $cookie)[0,1];
	$value =~ s/\\0/\n/g;
	$cookies{$key} = $value;
    }
    return %cookies;
}                                                                               

sub error_out {
    my %HTML = (ERROR => shift);
    print_form(template => "$path_templates/error.html", data => \%HTML);
}

# print html header
sub print_header {
    my %cookies = @_;

    return if $flag_header_sent;
   
    print "Content-type: text/html\n";
    foreach my $key (keys %cookies) {
	printf "Set-Cookie: %s=%s; PATH=;\n", $key, $cookies{$key};
    }
    print "\n";
    
    $flag_header_sent = 1;
}

# Substitute values on the specified template and print it to the client an
# optional 'type' arg can be passed: 'framed' specifies to pull in base.html
# as the outer frame and the given template as the inner frame 'single'
# specifies to use the given template alone the default behavior is 'framed'.
sub print_form {
    my %args = @_;
    
    $args{title} = $args{title} || 'Renewal Management';
    
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
	my $content = $template->output;
	$template = HTML::Template->new(
	    cache => 1,
	    filename => "$path_templates/base.html",
	    die_on_bad_params => 0,
	);
	$template->param(CONTENT => $content);
    }
    
    $template->param(
	CGI => $cgi,
	%{ $args{data} },
	user_id => $user_id,
    );

    print_header();
    print $template->output;
}

sub validate {
    my $ok = 0;
    if ($cookies{$COOKIE_NAME}) {
	my ($csum, $uid) = split /:/, $cookies{$COOKIE_NAME};
	if ($csum) {
	    $ok = compare($csum, $OPENSRS{private_key}, $uid);
	    $user_id = $uid if $ok;
	}
    } 
    return $ok;
}                                                                           

###########################################################

sub login {
    my $error_message = shift;
    
    my %HTML = ();
    $HTML{error_message} = $error_message;
    $HTML{cgi} = $cgi;

    print_form(template => "$path_templates/login.html", data => \%HTML);
}

sub logout {
    # reset global user_id and a cookie
    $user_id = 0;
    print_header($COOKIE_NAME => '');
    login();
}

sub do_login {
    if (not $in{username} or not $in{password}) {
	login('Authentication failed.');
	return;
    }

    my $result = $TPP_Client->login_user(
	$in{username}, $in{password}, $OPENSRS{username}
    );

    if (not defined $result or not $result->{is_success}) {
	login('Authentication failed.');
	return;
    }

    $user_id = $result->{attributes}{user_id};
    if (not $user_id) {
	error_out('Unable to get user information.');
	return;
    }
    
    my $csum = calculate($OPENSRS{private_key}, $user_id);
    
    print_header($COOKIE_NAME => "$csum:$user_id");

    main();
}

sub main {
    my %HTML = ();

    my $items = $TPP_Client->get_renewable_items(
	user_id => $user_id,
	requestor => $OPENSRS{username},
	days_before_expiry => $RENEWALS{cert}{days_before_expiry},
	days_after_expiry => $RENEWALS{cert}{days_after_expiry},
    );


    my $counter = 0;
    foreach my $item (@{$items}) {
	# XXX FIXME - we currently support certs' renewal only
	if ($item->{service} ne 'cert' or
		$item->{state} !~ /^(active|renewal_in_progress)$/) {
	    # mark item for later removal
	    $item->{inventory_item_id} = undef;
	    next;
	}

	$item->{even} = $counter++ % 2;
	
	$item->{active} = $item->{state} eq 'active' ? 1 : 0;	
	$item->{state} =~ s/_/ /g;
	$item->{state} = ucfirst $item->{state};
	
	$item->{description} = 'N/A' unless $item->{description};
	$item->{service} = ucfirst $item->{service};
	$item->{object_type} = ucfirst $item->{object_type};

	$item->{show_renewal_settings} = $RENEWALS{show_renewal_settings};
	$item->{renewal_ctrl} = $item->{renewal_ctl_mask} == 0 ? 'Let Expire' :
	    $item->{renewal_ctl_mask} == 1 ? 'Normal' : 'Auto Renew';
    }

    # remove marked items
    $items = [ grep { defined $_->{inventory_item_id} } @{$items} ];

    $HTML{show_renewal_settings} = $RENEWALS{show_renewal_settings};
    $HTML{items} = $items;
    $HTML{total} = scalar @{$items};
    
    print_form(template => "$path_templates/main.html", data => \%HTML);
}

sub check_renew {
    my %HTML = ();

    my $item = $TPP_Client->get_item(
	id => $in{id},
	requestor => $OPENSRS{username},
    );

    if (not $item or $item->{user_id} != $user_id) {
	error_out('Cannot find Inventory item ID #' . $in{id});
	return;
    }
    
    my $service = $item->{service};

    if (not exists $RENEWALS{$service} or not $RENEWALS{$service}{enabled}) {
	error_out(
	    'Product Item ID #' . $in{id} . ' cannot be renewed: ' .
	    $service . ' service is not configured or disabled.'
	);
	return;
    } elsif ($item->{state} ne 'active') {
	error_out(
	    'Product Item ID #' . $in{id} . ' cannot be renewed: ' .
	    'item is not active.'
	);
	return;
    }

    if ($RENEWALS{$service}{renew_url}) {
	# if defined external cgi for renewal processing -
	# re-direct request to its renew action along with
	# item's id.
	printf "Location: %s?action=renew&id=%d\n\n",
	    $RENEWALS{$service}{renew_url}, $in{id};
	return;
    }
}

# default renew action
sub renew {
    error_out('Default renew action is not implemented');
}
