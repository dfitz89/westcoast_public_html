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

# $Id: reg_cert.cgi,v 1.28 2006/07/05 18:24:34 mnieweglowski Exp $

use vars qw(
    %in $cgi $path_templates %actions $action %cc_types $TPP_Client
    %contact_keys %data @cc_types %CERT_CONTACT_FIELDS $user_id $COOKIE_NAME
    $flag_header_sent %cookies $path_to_config
);

# Null these things out for mod_perl users
(%in, $cgi, $path_templates, %actions, $action, %cc_types,
    @cc_types, $TPP_Client, %contact_keys, %data, $path_to_config) = ();

# pull in conf file with defined values
BEGIN {
    $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
    # first "do" the major config file
    do "$path_to_config/OpenSRS.conf";

    # now load up the config for Certificate service
    do "$path_to_config/Cert.conf";
}

use strict;
use lib $PATH_LIB;
use CGI ':cgi-lib';
use Email::Valid;
use HTML::Template;
use Data::Dumper;
use Core::Checksum qw(calculate compare);
use OpenSRS::TPP_Client;
use OpenSRS::ResponseConverter;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use OpenSRS::Util::Common qw(send_email build_select_menu build_select_menu3
			    build_country_list CODE_2_Country);

# global defines
$user_id = 0;
$COOKIE_NAME = "OPENSRS_TPP_CLIENT";
$flag_header_sent = 0;
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/reg_cert";
%in = ();

# list of valid actions to execute
%actions = (
    login => undef,
    do_login => undef,
    main => undef,
    collect_data => undef,
    verify_data => undef,
    register => undef,
    create_primary_contact => undef,
    renew => undef,
    logout => undef,
);

# List of mandatory contact fields
%CERT_CONTACT_FIELDS = (
    organization => {
	org_name => 1,
	address1 => 1,
	address2 => 0,
	address3 => 0,
	duns => 0,
	city => 1,
	state => 1,
	postal_code => 1,
	country => 1,
	phone => 1,
	fax => 1,
    },
    admin => {
	first_name => 1,
	last_name => 1,
	address1 => 1,
	city => 1,
	state => 1,
	postal_code => 1,
	country => 1,
	phone => 1,
	email => 1,
    }
);

# make tech and billing same as admin
$CERT_CONTACT_FIELDS{tech} = $CERT_CONTACT_FIELDS{admin};
$CERT_CONTACT_FIELDS{billing} = $CERT_CONTACT_FIELDS{admin};

%cc_types = (
    visa => 'Visa',
    mastercard => 'Mastercard',
    amex => 'American Express',
    discover => 'Discover',
);

@cc_types = qw(
    visa
    mastercard
    amex
    discover
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
    # if no action was supplied, use the defaults
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
    if ($REG_CERT{debug}) {
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
    
    $args{title} = $args{title} || 'Digital Certificate Registration';
    
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

# Credit Card bare-minimum validation
sub cc_verify {
    my $number = shift;

    $number =~ s/\D//g;

    return 0 unless length($number) >= 13 and int($number);

    my $weight;
    my $sum = 0;
    for (my $i = 0; $i < length($number) - 1; $i++) {
	$weight = substr($number, -1 * ($i + 2), 1) * (2 - ($i % 2));
	$sum += (($weight < 10) ? $weight : ($weight - 9));
    }

    if (substr($number, -1) == (10 - $sum % 10) % 10) {
	return 1;
    } else {
	return 0;
    }
}

sub cc_exp_verify {
    my ($cc_exp_mon, $cc_exp_yr) = @_;

    my ($month, $year) = (localtime)[4,5];
    $month++;
    $year += 1900;

    if (12 * $year + $month <= 12 * $cc_exp_yr + $cc_exp_mon) {
	return 1;
    } else {
	return 0;
    }
}

sub get_cc_years {
    my $year = 1900 + (localtime)[5];
    return ($year .. $year + 5);
}

sub get_approvers {
    my $domain = shift;

    my $request = {
	action => 'query',
	object => 'approver',
	requestor => {
	    username => $OPENSRS{username}
	},
	attributes => {
	    service => 'cert',
	    product_data => {
		domain => $domain,
	    }
	}
    };

    my $response = $TPP_Client->send_cmd($request);
    if (not defined $response or not exists $response->{is_success}) {
	error_out('Empty or invalid response from server');
	exit;
    } elsif ($response->{is_success} == 0) {
	error_out($response->{response_text} ||
	    'Unable to get approvers list');
	exit;
    }
   
    my $approver_list = $response->{attributes}{product_data}{approver_list};
    
    my (%result, %processed);
    foreach my $approver (@$approver_list) {
	# we use %processed hash to filter out duplicate emails in response
	unless (exists $processed{$approver->{type}.':'.$approver->{email}}) {
	    $processed{$approver->{type}.':'.$approver->{email}} = undef;
	    push @{$result{$approver->{type}}}, $approver->{email};
	}
    }
    
    return \%result;
}

sub populate_contact {
    my $source = shift;
    my $type = shift;

    my %contact = ();
    my @errors = ();
    foreach my $field (keys %{$CERT_CONTACT_FIELDS{$type}}) {
	my $required = $CERT_CONTACT_FIELDS{$type}{$field};
	my $value = $source->{$field};
	if ($required and not $value) {
	    push @errors,
		sprintf('%s field of %s contact must be specified',
		    ucfirst $field, ucfirst $type);
	}
	my $field_error = 0;
	if ($value) {
	    $field_error = 1 if ($field eq 'country' and $value !~ /^[a-zA-Z]{2}$/);
	    $field_error = 1 if ($field eq 'email' and 
		                        not (Email::Valid->rfc822($value) && $value !~ /@[^.]+$/));
	    $field_error = 1 if ($field eq 'phone' and not OpenSRS::Syntax::PhoneSyntax($value));
	    $field_error = 1 if ($field eq 'fax' and not OpenSRS::Syntax::PhoneSyntax($value));
	    push @errors, sprintf('Invalid %s field of %s contact', ucfirst $field, ucfirst $type) 
	                     if $field_error;
            if ($field =~ /first_name|last_name|org_name|city|state/) {
	        if ($value !~ /[a-zA-Z]/) {
		    push @errors, sprintf('%s field of %s contact must contain at least 1 alpha character',
		                      ucfirst $field, ucfirst $type);
		}
	    }
	}
	
	$contact{$field} = $value;
    }

    return (\%contact, \@errors);
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

sub do_login {
    my $result;

    if (not $in{username} or not $in{password}) {
	login('Authentication failed.');
	return;
    }

    if ($in{new_user}) {
	if ($in{password} ne $in{password1}) {
	    login('Passwords do not match. Please re-enter.');
	    return;
	}	
	# create new user
	$result = $TPP_Client->create_user(
	    $in{username}, $in{password}, $OPENSRS{username}
	);
    } else {
	# check if user exists
	$result = $TPP_Client->login_user(
	    $in{username}, $in{password}, $OPENSRS{username}
	);
    }

    if (not defined $result or not $result->{is_success}) {
	my $err = sprintf 'Failed to %s user: %s',
	    $in{new_user} ? 'create' : 'authenticate',
	    $result->{response_text} || 'Empty response from server';
	login($err);
	return;
    }

    $user_id = $result->{attributes}{user_id};
    if (not $user_id) {
	error_out('Unable to get user ID.');
	return;
    }
    
    # sign user_id and set the cooke.
    my $csum = calculate($OPENSRS{private_key}, $user_id);
    print_header($COOKIE_NAME => "$csum:$user_id");
    
    main();
}

sub logout {
    # reset global user_id and a cookie
    $user_id = 0;
    print_header($COOKIE_NAME => '');
    login();
}

sub main {    
    if ($in{new_user}) {
	return primary_contact_form();
    }
    
    my %HTML = ();
    $HTML{product_select} = '';

    my @products = @CERT_PRODUCTS;
    while (@products) {
	my $prod_code = shift @products;
	my $prod_name = shift @products;
	$HTML{product_select} .= sprintf "<option value=\"%s\">%s\n",
				    $prod_code, $prod_name;
    }
    
    print_form(template => "$path_templates/main.html", data => \%HTML);
}

sub collect_data {
    my %args = @_;
    my %HTML = %args;

    if ($args{errors}) {
	$HTML{errors} = join("<br>\n", @{$args{errors}});
    }

    # check for valid product
    if (not exists $CERT_PRODUCTS{ $in{product} }) {
	error_out('Invalid Product: ' . $in{product});
	return;
    }

    if (not $in{reg_type} or $in{reg_type} !~ /^(new|renewal)$/) {
	error_out('Invalid or missing registration type');
	return;
    }

    $HTML{reg_type} = $in{reg_type};

    if ($in{reg_type} eq 'renewal' and $in{id} =~ /^\d+$/) {
	# pull in product item details and populate %HTML with it
	
	# for wildcard certs renew() passes $item in %args, so no need to
	# fetch it again
	my $item = $args{item} || $TPP_Client->get_item(
	    id => $in{id},
	    requestor => $OPENSRS{username},
	);
	
	# XXX TODO move this sanity check to library
	if (not $item) {
	    error_out('Cannot find product item ID #' . $in{id});
	    return;
	}
	if ($item->{service} ne 'cert' or $item->{state} ne 'active') {
	    error_out('Product item ID #' . $in{id} . ' cannot be renewed.');
	    return;
	}

	if ($in{product} eq 'truebizidwildcard' and
		$item->{object_type} != 'truebizidwildcard') {
	    error_out('Incompatible upgrade to TrueBizIdWildcard');
	    return;
	}

	$in{domain} = $item->{product_data}{domain};
	$in{approver_email} = $item->{product_data}{approver_email};
	$in{csr} = $item->{product_data}{csr};
	$in{webserver} = $item->{product_data}{server_type};
	$HTML{csr_regenerate_forced} = $RENEWALS{csr_regenerate_forced_types}{$in{webserver}};

	for my $type qw(organization admin billing tech) {
	    $in{$type . '_contact_id'} = $item->{contact_set}{$type};
	}	
    }

    if ($in{product} =~ /^quickssl/) {
	# QuickSSL or QuickSSL Premium orders
	
	# XXX not the best regexp to check for a valid domain name
	$HTML{domain} = $in{domain};
	if ($in{domain} =~ /^\s*$/) {
	    error_out('Domain must be specified');
	    return;
	}
	    
	my @approvers = ();
	my $approvers = get_approvers($in{domain});
	$HTML{approvers_select} = '';
	foreach my $type (@APPROVER_TYPES) {
	    next unless exists $approvers->{$type};
	    foreach my $email (@{ $approvers->{$type} }) {
		$HTML{approvers_select} .=
		    sprintf "<option value=\"%s\"%s>%s (%s)\n",
			$email,
			$email eq $in{approver_email} ? ' selected' : '',
			$email,
			$type;
	    }
	}

	if (not $HTML{approvers_select}) {
	    error_out('No valid approvers found');
	    return;
	}

	$HTML{agreement_url} = $REG_CERT{quickssl_agreement_url};
    } else {
	# True BusinessID or True BusinessID Premium orders
	$HTML{organization_contact} = 1;
	$HTML{agreement_url} = $REG_CERT{truebizid_agreement_url};
	$HTML{organization_country_select} = build_country_list(
	    $in{organization_country}
	);
    }

    my $user_contacts =	$TPP_Client->get_user_contacts(
			    $user_id, $OPENSRS{username});
			
    if (not scalar(keys %{$user_contacts})) {
	error_out("Unable to get user contacts from server");
	return;
    }

    my %org_contacts = ();
    my %contacts = ();
    foreach my $contact_id (keys %{$user_contacts}) {
	my $contact = $user_contacts->{$contact_id};
	if ($contact->{email}) {
	    $contacts{$contact_id} = sprintf('%s, %s, %s',
		$contact->{last_name} || '',
		$contact->{first_name} || '',
		$contact->{email} || '',
	    );
	}
	if ($contact->{org_name} and $contact->{fax}) {
	    $org_contacts{$contact_id} = sprintf('%s, %s',
		$contact->{org_name},
		$contact->{email} || $contact->{fax}
	    );
	}
    }	

    $HTML{organization_contact_select} = build_select_menu(\%org_contacts,
	$in{organization_contact_id});
    $HTML{admin_contact_select} = build_select_menu(\%contacts,
	$in{admin_contact_id});
    $HTML{billing_contact_select} = build_select_menu3(
	{
	    %contacts,
	    same_as_admin => 'Same as Admin Contact',
	},
	['same_as_admin', keys %contacts],
	$in{billing_contact_id}
    );
    $HTML{tech_contact_select} = build_select_menu3(
	{
	    %contacts,
	    same_as_admin => 'Same as Admin Contact',
	    same_as_billing => 'Same as Billing Contact',
	},
	['same_as_admin', 'same_as_billing', keys %contacts],
	$in{tech_contact_id}
    );

    $HTML{id} = $in{id};
    $HTML{product} = $in{product};
    $HTML{product_name} = $CERT_PRODUCTS{ $in{product} };
    $HTML{csr_help_url} = $REG_CERT{csr_help_url};
    
    $HTML{admin_country_select} = build_country_list($in{admin_country});
    $HTML{billing_country_select} = build_country_list($in{billing_country});
    $HTML{tech_country_select} = build_country_list($in{tech_country});

    $HTML{period_select} = '';
    for (my $i = 1; $i <= $REG_CERT{max_period}; $i++) {
	$HTML{period_select} .= sprintf "<option value=\"%d\"%s>%d %s\n",
				    $i,
				    $i == $in{period} ? ' selected' : '',
				    $i,
				    $i == 1 ? 'Year' : 'Years';
    }

    $HTML{csr} = $in{csr};
    $HTML{webservers_select} = '';

    my @servers = @SERVER_TYPES;
    while (@servers) {
	my $webserver_code = shift @servers;
	my $webserver_name = shift @servers;
	$HTML{webservers_select} .=
	    sprintf "<option value=\"%s\"%s>%s\n",
		$webserver_code,
		$webserver_code eq $in{webserver} ? ' selected' : '',
		$webserver_name;
    }

    if ($in{billing_as_admin}) {
	$HTML{billing_as_admin} = 'checked';
    } else {
	$HTML{billing_as_admin} = '';
    }
    
    if ($in{tech_as_admin}) {
	$HTML{tech_as_admin} = 'checked';
	$HTML{tech_as_billing} = '';
    } elsif ($in{tech_as_billing}) {
	$HTML{tech_as_billing} = 'checked';
	$HTML{tech_as_admin} = '';
    }
   
    $HTML{renewal} = $in{reg_type} eq 'renewal';

    print_form(template => "$path_templates/cert_info.html", data => \%HTML);
}

sub verify_data {
    my %HTML = ();
    my @errors = ();

    $HTML{id} = $in{id};
    $HTML{reg_type} = $in{reg_type};
    $HTML{special_instructions} = $in{special_instructions};
    $HTML{product} = $in{product};
    $HTML{domain} = $in{domain};
    $HTML{approver_email} = $in{approver_email};
    $HTML{period} = $in{period};
    $HTML{csr} = $in{csr};
    $HTML{webserver} = $in{webserver};
    $HTML{show_cc_fields} = $F_SHOW_CC_FIELDS;
    
    if (not $in{period} or int($in{period}) > $REG_CERT{max_period}) {
	push @errors, 'Invalid period';
    }
    
    if ($in{product} =~ /^quickssl/) {
	# QuickSSL or QuickSSL Premium orders
	# check for required approver's email
	if (not $in{approver_email}) {
	    push @errors, 'Approver E-mail must be specified';
	}
    } else {
	# True BusinessID or True BusinessID Premium orders
	$HTML{organization_contact} = 1;
    }
    $HTML{product_name} = $CERT_PRODUCTS{ $in{product} };

    if ($in{webserver} and not exists $SERVER_TYPES{$in{webserver}}) {
	push @errors, 'Unknown Web Server';
    } else {
	$HTML{webserver_name} = $in{webserver} ?
				    $SERVER_TYPES{$in{webserver}} :
					'Not specified';
    }

    # validate contact info
    my %contact_id_map = ();
    foreach my $type qw(organization admin billing tech) {
	$HTML{$type . '_contact_id'} = $in{$type . '_contact_id'};
	if ($type eq 'organization' and $in{product} =~ /^quickssl/) {
	    # skip org. contact for quickssl products
	    next;
	} elsif ($in{$type . '_contact_id'}) {
	    my $value = $in{$type . '_contact_id'};
	    if ($value =~ /^same_as_(\w+)$/) {
		$HTML{$type . '_as_' . $1} = 1;
	    } else {
		# store type & contact_id for later processing
		$contact_id_map{$type} = $in{$type . '_contact_id'};
	    }
	} else {
	    my %contact_data =  map {
		$_ =~ /^${type}_(\w+)$/;
		$1 => $in{$_}
	    } grep { /^${type}_/ } keys %in;
	    
	    my ($contact, $contact_errors) =
		populate_contact(\%contact_data, $type);
		
	    push @errors, @{$contact_errors};
	    map { $HTML{$type . '_' . $_} = $contact->{$_} } keys %{$contact};
	    $HTML{$type.'_country_name'} = CODE_2_Country($contact->{country});
	}
    }

    if (scalar keys %contact_id_map) {
	my $user_contacts = $TPP_Client->get_user_contacts($user_id,
	    $OPENSRS{username});
	if (not $user_contacts) {
	    error_out("Unable to get user contacts from server");
	    return;
	}

	foreach my $type (keys %contact_id_map) {
	    my $contact_id = $contact_id_map{$type};
	    my ($contact, $contact_errors) = populate_contact(
		$user_contacts->{$contact_id},
		$type
	    );

	    push @errors, @{$contact_errors};
	    map { $HTML{$type . '_' . $_} = $contact->{$_} } keys %{$contact};
	    $HTML{$type.'_country_name'} = CODE_2_Country($contact->{country});
	}	
    }


    if (@errors) {
	collect_data(errors => \@errors, %in);
	return;
    }

    foreach my $mon (1 .. 12) {
	$HTML{cc_month_select} .= sprintf "<option value=\"%02d\">%02d\n",
				    $mon, $mon;
    }
    
    foreach my $year (get_cc_years()) {
	$HTML{cc_year_select} .= sprintf "<option value=\"%d\">%d\n",
				    $year, $year;
    }

    foreach my $cc_type (@cc_types) {
	$HTML{cc_type_select} .= sprintf "<option value=\"%s\">%s\n",
				    $cc_type, $cc_types{$cc_type};
    }

    print_form(template => "$path_templates/confirm_order.html",
	data => \%HTML);
}

sub register {
    my %HTML = ();

    if ($in{btnEdit}) {
	# Edit button was pressed - redirect to "Edit form"

	# make some cleanup if needed
	foreach my $type qw(organization admin billing tech) {
	    if ($in{$type . '_contact_id'} =~ /^(\d+)$/) {
		delete @in{
		    map {$type . '_' . $_} keys %{$CERT_CONTACT_FIELDS{$type}}
		}
	    }
	}

	collect_data(%in);
	return;
    }

    if ( $REG_CERT{F_VERIFY_CC} ) {

        # make a basic credit card validation
        if (not $cc_types{$in{cc_type}}) {
	    error_out('Non valid credit card');
	    return;
        } elsif ($in{cc_name} =~ /^\s*$/) {
	    error_out('Card Holder Name must be specified');
	    return;
        } elsif (not cc_verify($in{cc_num})) {
	    error_out('Non valid credit card');
	    return;
        } elsif (not cc_exp_verify($in{cc_mon}, $in{cc_year})) {
	    error_out('Non valid expiry date');
	    return;
        }
    }
    
    # gather contact info
    my @contacts = ();
    my %contact_set = ();
    foreach my $type qw(organization admin billing tech) {
	my %contact_data = ();	
	if ($type eq 'organization' and $in{product} =~ /^quickssl/) {
	    # skip org. contact for quickssl products
	    next;
	} elsif ($in{$type . '_as_admin'}) {
	    $contact_set{$type} = $contact_set{admin};
	    next;
	} elsif ($in{$type . '_as_billing'}) {
	    $contact_set{$type} = $contact_set{billing};
	    next;
	} else {
	    if ($in{$type .'_contact_id'}) {
		$contact_data{'id'} = $in{$type .'_contact_id'};
	    } else {
		foreach my $field (keys %{$CERT_CONTACT_FIELDS{$type}}) {
		    my $value = $in{$type .'_' . $field};
		    $contact_data{$field} = $value if $value;
		}
		$contact_data{client_reference} = 'client-' . time();
	    }
	}	
	push @contacts, \%contact_data;
	$contact_set{$type} = $#contacts;
    }
	
    # if there are any contacts referenced by contact_id - check them
    my @contact_id = map { $_->{id} || () } @contacts;	
    if (scalar @contact_id) {
	my $user_contacts = $TPP_Client->get_user_contacts($user_id,
	    $OPENSRS{username});
	if (not $user_contacts) {
	    error_out("Unable to get user contacts from server");
	    return;
	}
	my %id_map = map { $_ => undef } keys %{$user_contacts};
	foreach my $contact_id (@contact_id) {
	    if (not exists $id_map{$contact_id}) {
		error_out('Unable to locate Contact ID #' . $contact_id);
		return;
	    }
	}
    }

    my $request = {
	action => 'create',
	object => 'order',
	requestor => {
	    username => $OPENSRS{username},
	},
	attributes => {
	    handling => $REG_CERT{process_immediate} ? 'process' : 'save',
	    client_reference => 'client-'.time(),
	    user_id => $user_id,
	    contacts => \@contacts,
	    create_items => [
		{
		    client_reference => 'client-' . time(),
		    service => 'cert',
		    object_type => $in{product},		    
		    orderitem_type => $in{reg_type},
		    $in{reg_type} =~ 'renewal' ? (
			inventory_item_id => $in{id}
		    ) : (),
		    contact_set => \%contact_set,
		    product_data => {
			period => $in{period},
			csr => $in{csr},
			special_instructions => $in{special_instructions},
			server_type => $in{webserver},
			$in{approver_email} ? (
			    approver_email => $in{approver_email}
			) : (),
		    },
		}
	    ],
	},
    };

    my $response = $TPP_Client->send_cmd($request);

    if (not defined $response or not $response->{is_success}) {
	my $error_msg = 'Failed to create order: ';
        if ($response->{attributes}{order_id}){
	    $error_msg = "Order number is " . 
			 $response->{attributes}{order_id} . 
			 ".  ";
	}

	$error_msg .= $response->{response_text} ||
	    'Empty response from server';
	
	if ($REG_CERT{debug} and defined defined $response) {
	    $error_msg .= sprintf "<br>\nError details: %s",
		$response->{attributes}{create_items}->[0]->{major_text};
	}

	if (defined $response) {
	    # sometimes we may want to override default error message
	    # with specific one based on error code
	    my $code = int(
		$response->{attributes}{create_items}->[0]->{major_code}
	    );

	    if ($code == 3501) {
		# Provisioning communication error
		$error_msg =	"The server is currently down, so we can't " .
				"continue, but that is what we have so far.";
	    }
	}
	
	error_out($error_msg);
	return;
    }
    $HTML{response_code} = $response->{response_code};
    $HTML{response_text} = $response->{response_text};
    $HTML{order_id} = $response->{attributes}{order_id};
    $HTML{email} = $REG_CERT{inquires_email} || $ADMIN_EMAIL;
     if ($REG_CERT{send_order_placement_confirmation}) {
                send_email("$path_templates/order_placement_confirmation.txt",
                          {
                           %in,
                           mailfrom	    => $in{owner_email}||$ADMIN_EMAIL,
                           mailto	    => $ADMIN_EMAIL,
			   order_id	    => $response->{attributes}{order_id},
			   order_item_id    => $response->{attributes}{create_items}->[0]->{item_id},
			   p_cc_type        => $in{cc_type},
			   p_cc_name        => $in{cc_name},
			   p_cc_num         => $in{cc_num},
			   p_cc_exp_mon     => $in{cc_mon},
			   p_cc_exp_yr      => $in{cc_year},
                           });
    }


    print_form(template => "$path_templates/result.html", data => \%HTML);
}

sub primary_contact_form{
    my %args = @_;

    my %HTML = ();

    if ($args{errors}) {
        $HTML{errors} = join("<br>\n", @{$args{errors}});
    }
    $HTML{country_select} = build_country_list($in{country});
    foreach (qw/first_name last_name title org_name 
		address1 address2 address3 city state postal_code
		phone fax email url/){
	$HTML{$_} = $in{$_};
    }
    print_form( template => "$path_templates/primary_contact.html", 
		data => \%HTML
    );
}

sub create_primary_contact {

    my ($contact, $contact_errors) = populate_contact(\%in, 'admin');

    if (scalar @{$contact_errors}){
	return primary_contact_form( errors => $contact_errors );
    }
    
    #create_contact
    my $result = $TPP_Client->send_cmd({
        action => 'create',
        object => 'contact',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
            user_id => $user_id,
            contacts => [$contact]
        },
    });

    if (not defined $result or not $result->{is_success}) {
	my $err = sprintf 'Failed to create contact: %s',
	    $result->{response_text} || 'Empty response from server';
	error_out($err);
	return;
    }

    main();
}

sub renew {
    my %HTML = ();

    if (not $REG_CERT{renewals_enabled}) {
	error_out("Renewal processing is disabled.");
	return;
    }

    if (not $in{id}) {
	error_out('Item ID# must be specified.');
	return;
    }
    
    my $item = $TPP_Client->get_item(
	id => $in{id},
	requestor => $OPENSRS{username},
    );                                                                          

    # XXX TODO move this sanity check to library
    if (not $item) {
	error_out('Cannot find product item ID #' . $in{id});
	return;
    }                                                                           
    if ($item->{service} ne 'cert' or $item->{state} ne 'active') {
	error_out('Product item ID #' . $in{id} . ' cannot be renewed.');
	return;
    }

    if ($item->{object_type} eq 'truebizidwildcard') {
	# we don't allow product upgrade/downgrade for 'truebizidwildcard'
	# certs, so call collect_data() directly.

	# $in{id} is already set
	$in{reg_type} = 'renewal';
	$in{product} = $item->{object_type};

	collect_data(item => $item);
	return;
    }

    $HTML{id} = $item->{inventory_item_id};
    $HTML{domain} = $item->{product_data}{domain};

    my @products = @CERT_PRODUCTS;
    while (@products) {
	my $prod_code = shift @products;
	my $prod_name = shift @products;

	# skip truebizidwildcard
	next if $prod_code eq 'truebizidwildcard';
	
	$HTML{product_select} .= sprintf "<option value=\"%s\"%s>%s\n",
	    $prod_code,
	    $item->{object_type} eq $prod_code ? ' selected' : '',
	    $prod_name;
    }
    
    print_form(template => "$path_templates/renew.html", data => \%HTML);
}
