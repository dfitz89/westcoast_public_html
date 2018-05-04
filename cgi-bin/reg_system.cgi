#!/usr/local/bin/perl

#       .Copyright (C)  1999-2002 TUCOWS.com Inc.
#       .Created:       11/19/1999
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Originally Developed by:
#                       VPOP Technologies, Inc. for Tucows/OpenSRS
#       .Authors:       Joe McDonald, Tom McDonald, Matt Reimer, Brad Hilton,
#                       Daniel Manley, Evgeniy Pirogov
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
	    %in $cgi $path_templates %actions $action %cc_types $XML_Client
	    %contact_keys %data %cc_mons @cc_types $path_to_config
	   );
(      %in, $cgi, $path_templates, %actions, $action, %cc_mons, %cc_types, $XML_Client,
        %contact_keys, %data ) = ();

# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
    $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
    if ($ENV{OSRS_CLIENT_ETC}){
        $path_to_config = "$ENV{OSRS_CLIENT_ETC}";
    } 
    do "$path_to_config/OpenSRS.conf"; 
}
use strict;
use Data::Dumper;
use lib $PATH_LIB;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use CGI ':cgi-lib';

use OpenSRS::XML_Client qw(:default);
use OpenSRS::Util::Common qw(send_email build_select_menu build_select_menu3 locale_build_country_list);
use OpenSRS::Util::America qw(build_app_purpose_list);
use OpenSRS::Util::Europe qw(build_eu_countries_list build_eu_languages_list build_be_languages_list);
use OpenSRS::Util::Asia qw(%asia_ced_locality_country %asia_ced_contact_type %asia_ced_entity_type %asia_ced_identification_type
                           build_ced_contact_type_select_list build_ced_locality_select_list
                           build_ced_entity_type_select_list build_ced_identification_type_select_list);
use OpenSRS::Language qw/native_to_puny puny_to_native code2language/;

# global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/reg_system";
%in = ();

# list of valid actions to execute
%actions = (
	    lookup => undef,
	    check_transfer => undef,
	    
	    setup_profile => undef,
	    do_setup_profile => undef,
	    
	    verify_order => undef,
	    register => undef,
	    
	    bulk_order => undef,
	    bulk_order_ca => undef,
	    bulk_order_us => undef,
	    bulk_order_asia => undef,
	    bulk_transfer => undef,
	    do_bulk_transfer => undef, 
	   );

%cc_types = (
	     visa => "Visa",
	     mastercard => "Mastercard",
	     amex => "American Express",
	     discover => "Discover",
	    );

@cc_types = qw (visa mastercard amex discover);
 
%cc_mons = (1=>"01", 2=>"02", 3=>"03", 4=>"04", 5=>"05", 6=>"06", 7=>"07",
		8=>"08",9=>"09",10=>"10",11=>"11",12=>"12",);

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
		 lang => undef,
		 vat => undef,
    	    	);

###############################################
###############################################

print "Content-type:  text/html\n\n";

# set debugging level
start_up();

# create a client object which we will use to connect to the OpenSRS server
$XML_Client = new OpenSRS::XML_Client(%OPENSRS);
$XML_Client->login;

# read in the form data
ReadParse(\%in);

$action = $in{action};

# no action was supplied, so use the default
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

# close connection to the server
$XML_Client->logout;

exit;

####################################################################
### Begin subroutines
###################################################################

######################################################
## First, subroutines you may wish to adjust...
#####################################################

sub start_up {

    if ($REG_SYSTEM{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
    
    OpenSRS::Util::Common::initialize(path_templates => $PATH_TEMPLATES);
}

sub main_menu {
    my (%HTML, $mldns);
    # no action was specified, so print main page

    $HTML{CGI} = $cgi;
    $HTML{affiliate_id} = $in{affiliate_id};

    #
    # MLDNS requires extra stuff...
    #
    #createMLDNSHTMLLink (\%HTML);

    if ( $REG_SYSTEM{ F_SUPPORT_CERTS } ) {
        $HTML{ CERT_FORM } = get_content( "$path_templates/cert_request.html", {%HTML, WEB_CERT_CGI => $REG_SYSTEM{WEB_CERT_CGI } } );
    }

    print_form("$path_templates/main_menu.html",\%HTML);
}

sub verify_order {
    # check fields for proper data
    
    my ($key,$cleaned_value,$error_msg,$domain_string,$domain,@domains);
    my (%good_domains,%bad_domains,%domains,$type,$field,$num,$fqdn,$nameservers);
    my ($punycodeObj, $originalDomain, $formCountry);
    my ($lookup_data);

    my %HTML = %in;    
    my $cc_num = $in{p_cc_num};
    my $cc_type = $in{p_cc_type};
    my $cc_exp_mon = $in{p_cc_exp_mon};
    my $cc_exp_yr = $in{p_cc_exp_yr};
    
    ##################################################################
    # here we check the validity of the cc_number, both its length
    # and its validity
    
    # only run this test if you set F_VERIFY_CC in conf file
    if ($REG_SYSTEM{F_VERIFY_CC}) {

	# check the cc number
	if (not cc_verify($cc_num)) {
	    error_out("Invalid credit card number.\n");
	    exit;
	}

	# check the expiration date
	if (not cc_exp_verify($cc_exp_mon,$cc_exp_yr)) {
	    error_out("Invalid credit card expiration: $cc_exp_mon/$cc_exp_yr.\n");
	    exit;
	}
    }
    if ( $F_SHOW_CC_FIELDS ) {
        $HTML{VERIFY_CC_FIELDS} = get_content("$path_templates/verify_cc_fields.html", { p_cc_num     => $cc_num,
                                                                                         p_cc_type    => $cc_type,
                                                                                         p_cc_exp_mon => $cc_exp_mon,
                                                                                         p_cc_exp_yr  => $cc_exp_yr, }
                                             );
    }

    # check for reg_username and reg_password
    if (not $in{reg_username}) {
	error_out("No username supplied");
	exit;
    } elsif (not $in{reg_password}) {
	error_out("No password supplied");
	exit;
    } elsif (defined $in{reg_password_confirm} and $in{reg_password} ne $in{reg_password_confirm}) {
	error_out("Password mismatch");
	exit;
    }
    
    ##################################################################
    ##################################################################
    
    ###################################
    # check syntax on domains given if this is a bulk order
    my ($gtld,$ca,$uk,$us,$asia,$de,$eu,$be);

    my $mldn = 0;
    my $ascii = 0;

    if ($in{bulk_order}) {	# this is a bulk order
	my $domains = $in{domains};
	my $syntaxError = undef;
	$domains =~ s/\r//g;
	$domains =~ s/\n/ /g;
	$domains =~ s/,/ /g;
	@domains = split /\s+/, $domains;
 
	$error_msg = "";

	foreach $domain (@domains) {
            #
	    # check for duplicates
            #
	    if (exists $domains{$domain}) {
		$bad_domains{$domain} = "Duplicate domain.";
		next;
	    }	

            $punycodeObj = native_to_puny($domain, \%OPENSRS);

	    if ($punycodeObj ne $domain) {
		$mldn = 1;
	    } else {
		$ascii = 1;
	    }
	    
	    $gtld = $gtld || $punycodeObj =~ /(com|net|org)$/i;
	    $ca   = $ca   || $punycodeObj =~ /ca$/i;
	    $de   = $de   || $punycodeObj =~ /de$/i;
	    $us   = $us   || $punycodeObj =~ /us$/i;
	    $asia = $asia || $punycodeObj =~ /asia$/i;
	    $uk   = $uk   || $punycodeObj =~ /uk$/i;
	    $eu   = $eu   || $punycodeObj =~ /eu$/i;
	    $be   = $be   || $punycodeObj =~ /be$/i;

            #
            # Check syntax.
            #
            if ($syntaxError = check_domain_syntax($punycodeObj))
            {
               $bad_domains{$originalDomain} = $syntaxError;
               next;
            }

	    $lookup_data = {
			    action => "lookup",
			    object => "domain",
			    attributes => {
				domain => $punycodeObj,
				affiliate_id => $in{affiliate_id},
				}
			   };

	    # add the domain to the hash to check for duplicates
	    $domains{$domain} = 1;

	    if ($in{reg_type} eq 'new') {
		my $lookup_results = $XML_Client->send_cmd( $lookup_data );
		if ($lookup_results->{attributes}->{status} eq 'taken') {
		    $bad_domains{$domain} = "Domain taken.";
		    next;
		}
		if ($lookup_results->{attributes}->{status} eq 'invalid') {
		    unless ($F_QUEUE_SUPPLIER_UNAVAILABLE) {
			$bad_domains{$domain} = "Error checking domain [".$lookup_results->{response_text}."].";
			next;
		    }
		}
	    } else {
		$lookup_data->{action} = "check_transfer";
		$lookup_data->{object} = "domain";
		my $lookup_results = $XML_Client->send_cmd( $lookup_data );
		if ($lookup_results && $lookup_results->{is_success} == 1) {
		    if ( $lookup_results->{attributes}->{transferrable} != 1 and
			 !( $lookup_results->{attributes}->{noservice} and
			    $F_QUEUE_SUPPLIER_UNAVAILABLE 
			  )
		    ) {
			$bad_domains{$domain} = "Domain not transferable: $lookup_results->{attributes}->{reason}.";
			next;
		    }
		} else {
		    $bad_domains{$domain} = "Domain not transferable: Error in check transfer [$lookup_results->{response_text}].";
		    next;
		}
	    }
	    $good_domains{$domain} = 1;
	}

	if ( $ascii and $mldn and $in{ reg_type } eq 'transfer' ) {
	    $error_msg = "Bulk transfer requests cannot contain both ASCII and multi-lingual domains";
	}
	if ($ca and ($gtld or $uk or $us or $asia or $de)){
	    $error_msg = "You can't mix .ca with gTLD or .uk domains in bulk_registration";
	}

	if ($us and ($gtld or $uk or $ca or $de)){
	    $error_msg = "You can't mix .us with gTLD, .ca or .uk domains in bulk_registration";
	}

	if ($asia and ($gtld or $uk or $ca or $de or $us)){
	    $error_msg = "You can't mix .asia with gTLD, .ca, .de, .us or .uk domains in bulk_registration";
	}

	if ($de and ($gtld or $uk or $ca or $us or $asia)){
	    $error_msg = "You can't mix .de with gTLD, .ca or .uk domains in bulk_registration";
	}

	if ($ca and $in{reg_domain} !~ /ca$/i and $in{reg_type} eq 'new'){
	    $error_msg = "Bulk registration for .ca must be based on a previously registered .ca domain";
	}

	# if they didn't provide any good domains, error out now
	if (not keys %good_domains and keys %bad_domains) {
	    $error_msg = join("", map { "$_: $bad_domains{$_}<br>\n" } keys %bad_domains);
	}

	if ($error_msg) {
	    error_out($error_msg);
	    exit;
	}

    } else {
	# this isn't a bulk order, but we still need to allow for a person
	# registering multiple domains with different tlds
	%good_domains = map { $_, 1 } split /\0/, $in{domain};
	map {	    $gtld = $gtld || $_ =~ /(com|net|org|info|biz)$/i;
		    $ca   = $ca   || $_ =~ /ca$/i;
		    $de   = $de   || $_ =~ /de$/i;
		    $uk   = $uk   || $_ =~ /uk$/i;
		    $us   = $us   || $_ =~ /us$/i;
		    $asia = $asia || $_ =~ /asia$/i;
		    $eu   = $eu   || $_ =~ /eu$/i;
		    $be   = $be   || $_ =~ /be$/i;
		} keys %good_domains;
	if ($eu and ($gtld or $uk or $us or $asia or $de)){
	    error_out("You can't mix .eu with gTLD, .us, .asia, or .uk domains in bulk_registration");
	    exit;
	}elsif ($be and ($gtld or $uk or $us or $asia or $de)){
	    error_out("You can't mix .be with gTLD, .us, .asia, or .uk domains in bulk_registration");
	    exit;
	} elsif ($ca and ($gtld or $uk or $us or $asia or $de)){
	    error_out("You can't mix .ca with gTLD, .us, .asia, or .uk domains in bulk_registration");
	    exit;
	} elsif ($us and ($gtld or $uk or $ca or $de)){
	    error_out("You can't mix .us with gTLD, .ca, or .uk domains in bulk_registration");
	    exit;
	} elsif ($asia and ($gtld or $uk or $ca or $de or $us)){
	    error_out("You can't mix .asia with gTLD, .ca, .us, or .uk domains in bulk_registration");
	    exit;
	} elsif ($de and ($gtld or $uk or $ca or $us or $asia)){
	    error_out("You can't mix .de with gTLD, .ca, .us, .asia, or .uk domains in bulk_registration");
	    exit;
	} elsif ( $ca  and $in{reg_type} eq 'new' ) {
	    # for .ca domains, ensure a valid legal type was given
	    if ( $in{ legal_type } eq '' ) {
		error_out( 'No legal type selected' );
		exit;
	    }

	    if ( not exists $CA_LEGAL_TYPES{ $in{ legal_type } } ) {
		error_out( 'Invalid legal type selected.' );
		exit;
	    }
	} # .us validation for nexus is done in XML_Client::validate()
    }
    my @converted_list = ();
    foreach $domain (keys %good_domains) {
	$domain_string .= "<input type=hidden name=domain value=\"$domain\">\n";	
	push @converted_list,native_to_puny($domain, \%OPENSRS);
    }
    $HTML{domain} = join "\0", @converted_list;

    if ( $in{reg_type} eq 'new' and  
	 $HTML{domain} =~ /xn--.+\.(?:com|net|de|org|biz|cc|tv|info)/ ) {
	
	if ( $in{language_tag} ) {
    
            my $language = code2language($in{language_tag}) ;
            $HTML{language} = <<EOF;
<tr>
    <td align=right><b>Language:</b></td>
    <td>$language</td>
    <input type=hidden name='language_tag' value='$in{language_tag}'
</tr>
EOF
        } else {
	    error_out( "Encoded domains must have a language selected." );
	    exit;
	}
    } 

    if ($in{email_bundle}) {
	$domain_string .= "<input type=hidden name=forwarding_email value=\"$in{forwarding_email}\">\n";
    }

    if ( ( not $in{reg_type} eq 'transfer' ) or
         ( not $ca ) ) {
	# do not check transfer for .ca
	# copy over the normal contact info to 'admin', 'billing' and/or 'tech' info 
	# if they had that flag set
	if (defined $in{flag_admin_use_contact_info} and 
	    $in{flag_admin_use_contact_info}) {
	    foreach $key (keys %in) {
		if ($key =~ /^admin_(.+)$/) {
		    $in{"admin_$1"} = $in{"owner_$1"};
		    $HTML{$key} = $in{"owner_$1"};
		}
	    }
	}

	if (defined $in{flag_billing_use_contact_info} and 
	    $in{flag_billing_use_contact_info}) {
	    foreach $key (keys %in) {
		if ($key =~ /^billing_(.+)$/) {
		    $in{"billing_$1"} = $in{"owner_$1"};
		    $HTML{$key} = $in{"owner_$1"};
		}
	    }
	} elsif (defined $in{flag_billing_use_admin_info} and 
	    $in{flag_billing_use_admin_info}){
	    foreach $key (keys %in) {
		if ($key =~ /^billing_(.+)$/) {
		    $in{"billing_$1"} = $in{"admin_$1"};
		    $HTML{$key} = $in{"admin_$1"};
		}
	    }
	}
	

	if ($REG_SYSTEM{custom_tech_contact}){
	    if (defined $in{flag_tech_use_contact_info} and
		$in{flag_tech_use_contact_info}) {
		foreach $key (keys %in) {
		    if ($key =~ /^tech_(.+)$/) {
			$HTML{$key} = $in{"owner_$1"};
		    }
		}
	    } elsif (defined $in{flag_tech_use_admin_info} and
		     $in{flag_tech_use_admin_info}) {
		foreach $key (keys %in) {
		    if ($key =~ /^tech_(.+)$/) {
			$HTML{$key} = $in{"admin_$1"};
		    }
		}
	    } elsif (defined $in{flag_tech_use_billing_info} and
		     $in{flag_tech_use_billing_info}) {
		foreach $key (keys %in) {
		    if ($key =~ /^tech_(.+)$/) {
			$HTML{$key} = $in{"billing_$1"};
		    }
		} 
	    }
	}

	# use library to verify the supplied data
	my ($custom_nameservers);
	if ($in{reg_type} eq 'new' and $REG_SYSTEM{custom_nameservers}) {
	    $custom_nameservers = 1;
	} else {
	    $custom_nameservers = 0;
	}
	
	# insert the domains into $HTML{domain} for the validation code below
	
	my $custom_verify='default';
	if ($ca) {
	    $custom_verify='ca';
	} elsif ($de) {
	    $custom_verify='de';
	} elsif ($uk and $in{reg_type} eq 'transfer' and !$in{change_contact}){
	    $HTML{admin_email} = $in{no_change_contact_admin_email};
	    $custom_verify='uk';
	} elsif ($uk) {
	    $custom_verify='uk';
	} elsif ($be){
	    $custom_verify='be';
	} elsif ($eu){
	    $custom_verify='eu';
	}

	my %verify_results = $XML_Client->validate(
	    \%HTML, 
	    custom_tech_contact => $REG_SYSTEM{custom_tech_contact}, 
	    custom_nameservers => $custom_nameservers,
	    custom_verify => $custom_verify 
	);
	
	if (not $verify_results{is_success}) {
	    # there were problems with submitted data...
	    $error_msg = $verify_results{error_msg};
	    error_out($error_msg);
	    exit;
	}

	# everything looks in order... so far...
	# pass along the tech contact info if the conf file tells us to
	# use %HTML so that "flag_tech_use_contact_info" is applied
	if ($REG_SYSTEM{custom_tech_contact}) {
	    $HTML{TECH_CONTACT} = build_tech_verify(\%HTML);
	}
	
	# add 'tech' as a contact type if the conf file has that defined
	my @contact_types = ('owner','admin','billing');
	if ($REG_SYSTEM{custom_tech_contact}) {
	    push @contact_types, 'tech';
	}
	# encode the contact info and pass it to the next form
	
	foreach $type (@contact_types) {
	    my @contact_fields = qw(first_name last_name org_name address1 address2 address3 city state postal_code country email phone fax);
	    if ($HTML{domain} =~ /(eu|be)$/i){ 
		push @contact_fields, 'vat', 'lang';
	    }
	    foreach $field (@contact_fields) {
		$HTML{CONTACT_INFO} .= "<input type=hidden name=\"${type}_$field\" value=\"" . encode($HTML{"${type}_$field"}) . "\">\n";
	    }
	}
	
	# make the display of this data look a little better
	if ($HTML{owner_address2}) { $HTML{owner_address2} .= "<br>\n" }
	if ($HTML{owner_address3}) { $HTML{owner_address3} .= "<br>\n" }
	if ($HTML{billing_address2}) { $HTML{billing_address2} .= "<br>\n" }
	if ($HTML{billing_address3}) { $HTML{billing_address3} .= "<br>\n" }
	
	# encode the nameserver info and pass it to the next form
	if ($custom_nameservers) {
	    foreach $num (1..6) {
		$fqdn = $in{"fqdn$num"};
		if ($fqdn) {
		    $nameservers .= "$fqdn <br>\n";
		    $HTML{NAMESERVER_INFO} .= "<input type=hidden name=\"fqdn$num\" value=\"" . encode($fqdn) . "\">\n";
		}
	    }
	    
	    $HTML{NAMESERVERS} = <<EOF;
	    <tr><td colspan=2 align=center><b>Nameserver Information</b></td></tr>
	    <tr><td colspan=2 align=center>$nameservers</td></tr>
EOF
	}

	if ($REG_SYSTEM{allow_auto_renew}) {
	    $HTML{BILLING_INFO} .= "<input type=hidden name=\"auto_renew\" value=\"" . encode($in{auto_renew}) . "\">\n";
	}
    }

    # encode the billing info and pass it to the next form
    $HTML{BILLING_INFO} .= "<input type=hidden name=\"p_cc_num\" value=\"" . encode($cc_num) . "\">\n"; 
    $HTML{BILLING_INFO} .= "<input type=hidden name=\"p_cc_type\" value=\"" . encode($cc_type) . "\">\n";
    $HTML{BILLING_INFO} .= "<input type=hidden name=\"p_cc_exp_mon\" value=\"" . encode($cc_exp_mon) . "\">\n";
    $HTML{BILLING_INFO} .= "<input type=hidden name=\"p_cc_exp_yr\" value=\"" . encode($cc_exp_yr) . "\">\n";
    
    # display the cc_type using our %cc_types hash at the top of the
    # script
    $HTML{p_cc_type} = $cc_types{$in{p_cc_type}};
    
    $HTML{domains} = join("<br>\n", keys %good_domains);
    $HTML{forwarding_email} = $in{forwarding_email};
    if (keys %bad_domains) {
	$HTML{bad_domains} = "<b>Invalid Domains:</b><br>\n" . join("", map { "<font color=red>$_: $bad_domains{$_}</font><br>\n" } keys %bad_domains) . "<br>\n";;
    }
    

    $HTML{domain_string} = $domain_string;
    $HTML{CGI} = $cgi;
    $HTML{affiliate_id} = $in{affiliate_id};
    $HTML{period_text} = $REG_PERIODS{$in{period}};
    $HTML{reg_username} = encode($in{reg_username});
    $HTML{reg_password} = encode($in{reg_password});
    $HTML{reg_domain} = encode($in{reg_domain});
    $HTML{reg_type} = $in{reg_type};
    
    if ($REG_SYSTEM{allow_auto_renew}) {
	my $renew_value = $in{auto_renew} ? 'Yes':'No';
	$HTML{auto_renew_section} = <<EOF;
<tr>
<td align=right><b>Auto-renew:</b></td>
<td>$renew_value</td>
</tr>
EOF
    }

    if ($in{reg_type} eq 'new') {
	$HTML{reg_type_text} = 'New Domain';
	$HTML{action} = 'register';
    } else {
	if ($in{bulk_order}) {
	    $HTML{reg_type_text} = 'Batch Transfer';
	    $HTML{ mldn } = $mldn || 0;
	    $HTML{action} = 'do_bulk_transfer';
	} else {
	    $HTML{reg_type_text} = 'Transfer';
	    $HTML{action} = 'register';
	}
    }
    
    my $whois_privacy_value = $in{f_whois_privacy} ? 'Yes' : 'No';
    $HTML{whois_privacy_section} = <<EOF;
<tr>
<td align=right><b>Whois Privacy:</b></td>
<td>$whois_privacy_value
<input type=hidden name=f_whois_privacy value=$in{f_whois_privacy}>
</td>
</tr>
EOF
    if ( $MANAGE{allow_domain_locking} and not $in{bulk_order} ) {
	    my $lock_value = $in{f_lock_domain} ? 'Yes' : 'No';
	    $HTML{domain_locking_section} = <<EOF;
<tr>
<td align=right><b>Lock domain:</b></td>
<td>$lock_value
<input type=hidden name=f_lock_domain value=$in{f_lock_domain}>
</td>
</tr>
EOF
    }


    if ( $ca and $in{reg_type} eq 'transfer') {
	print_form("$path_templates/verify_ca_transfer.html",\%HTML);
	return;
    }

    if ( $ca ) {
    	$formCountry = "_ca";
	
	$HTML{isa_trademark} = $in{isa_trademark} ? "Yes" : "No";
	$HTML{want_cira_member} = $in{cira_member} eq 'Y'  ? "Yes" : "No";
	$HTML{domain_description} = $in{domain_description} ? $in{domain_description} : "<I>-none-</I>";
	$HTML{domain_description} =~ s/\n/<BR>/g;

    	$HTML{legal_type} = $CA_LEGAL_TYPES{$in{legal_type}};
	$HTML{lang_pref} = ( $in{lang_pref} eq "EN" ) ? "English" : "Français";

	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="lang_pref" value="' . $in{lang_pref} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="cira_member" value="' . $in{cira_member} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="isa_trademark" value="' . ( $in{isa_trademark} ? $in{isa_trademark} : "0" ) . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="legal_type" value="' . $in{legal_type} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="domain_description" value="' . $in{domain_description} . "\">\n";
	
    } elsif ( $us ) {
    	my $ccodes;
        $formCountry = "_us";

        $HTML{app_purpose} = $OpenSRS::Util::America::america_application_purposes{$in{app_purpose}};
        $HTML{nexus_category} = $OpenSRS::Util::America::america_nexus_categories{$in{nexus_category}};
        if ( $in{nexus_validator} ) {
            $HTML{nexus_validator} = $in{nexus_validator};
            $HTML{nexus_validator} .= " - ".OpenSRS::Util::Common::CODE_2_Country($in{nexus_validator});
        } else {
            $HTML{nexus_validator} = "Not Applicable";
        }
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="app_purpose" value="' . $in{app_purpose} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="nexus_category" value="' . $in{nexus_category} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="nexus_validator" value="' . $in{nexus_validator} . "\">\n";
    } elsif ( $asia ) {
    	my $ccodes;
        $formCountry = "_asia";

        # Show the data on the page NICELY...
	$HTML{ced_contact_type} = $asia_ced_contact_type{$in{ced_contact_type}};
	$HTML{ced_locality_country} = $asia_ced_locality_country{$in{ced_locality_country}};
	if($in{ced_legal_entity_type} eq 'other') {
	    $HTML{ced_legal_entity_type}=$in{ced_legal_entity_type_info};
	} else {
	    $HTML{ced_legal_entity_type}=$asia_ced_entity_type{$in{ced_legal_entity_type}};
	}
	if($in{ced_id_type} eq 'other') {
	    $HTML{ced_id_type}=$in{ced_id_type_info};
	} else {
	    $HTML{ced_id_type}=$asia_ced_identification_type{$in{ced_id_type}};
	}

        # Make sure the data is passed to the next screen...
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_contact_type" value="' . $in{ced_contact_type} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_locality_country" value="' . $in{ced_locality_country} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_locality_city" value="' . $in{ced_locality_city} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_locality_state_prov" value="' . $in{ced_locality_state_prov} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_legal_entity_type" value="' . $in{ced_legal_entity_type} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_legal_entity_type_info" value="' . $in{ced_legal_entity_type_info} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_id_type" value="' . $in{ced_id_type} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_id_type_info" value="' . $in{ced_id_type_info} . "\">\n";
	$HTML{SPECIAL_DOMAIN_INFO} .= '<input type=hidden name="ced_id_number" value="' . $in{ced_id_number} . "\">\n";

    } elsif ( $in{domain} =~ /name$/ && $in{email_bundle} == 1) {
	$formCountry = "_name";
    } elsif ( $in{domain} =~ /eu$/ ) {
	$formCountry = "_eu";
    } elsif ( $in{domain} =~ /be$/ ) {
	$formCountry = "_be";
    } elsif ( $in{domain} =~ /de$/) {
	if( $in{reg_type} eq 'transfer' ){
	     $formCountry = "_de_transfer";
	} else {
	    $formCountry = "_de";
	}
    } elsif ( $in{domain} =~ /.uk$/ and $in{reg_type} eq 'transfer' ) {
	$formCountry = "_uk_transfer";
    } else {
    	$formCountry = "";
    }

    print_form("$path_templates/verify$formCountry.html",\%HTML);
}

########################################################
# dynamically build all .ca legal types.
sub build_ca_domain_legal_types
{
   my $type	= shift;
   my ($selected, $key);

   $selected = $type ? "" : "selected";
   my $string	= qq(   <option value="" $selected>select legal type\n);

   foreach $key (@CA_LEGAL_TYPES_ORDER)
   {
      $selected	= "";
      $selected	= " selected " if ($type =~ /$key/i);
      $string	.= "   <option value=\"$key\" $selected>$CA_LEGAL_TYPES{$key}\n";
   }

   return $string;
}


sub register {
    
    my (%HTML,$key,$xcp_request,$register_results,$error);
    my ($domain,$status,$id,$link_domains,$reg_type);
    my ($punycodeObj, $revDomain);
   
    $xcp_request = {
    		action => "sw_register",
		object => "domain",
		attributes => { 
#Uncomment one of the string or pass a specific value of parameter
#If not passed or value not save|process then settings from RSP profile will be used
#		    handle => 'save',  #save order only regardless RSP settings
#		    handle => 'process', #process order always regardless RSP settings 

		    contact_set => {},
		    nameserver_list => [],
		    },
    		};

    # clean up data that was posted, stick it in %data
    foreach $key (keys %in) {
	$in{$key} = unencode($in{$key});
    }

    if($in{RejectButton} eq "DECLINE") {
	print "Thank you for using OpenSRS.<BR>";
	exit;
    }

    my $sortorder = 1;
    # clean up data that was posted, stick it in %data
    foreach $key ( sort keys %in) {

	next if $key eq "domain";
	next if $key eq "handle";  #to prevent hacking from form

    	if ( $key =~ /^(owner|billing|tech|admin)_/i )
	{
	    my $contact_type = $1;
	    my $contact_key = $key;
	    $contact_key =~ s/^(owner|billing|tech|admin)_//i;
	    if  ( exists $contact_keys{$contact_key} )
	    {
    	    	$xcp_request->{attributes}->{contact_set}->{$contact_type}->{$contact_key} =
		    	$in{$key};
	    }
	    next;
	}
    	
        #
        # Push the name servers list.
        #
    	if ( $key =~ /^fqdn\d+$/i )
	{
	    if  ( defined $in{$key} )
	    {
				# ikolomiets: Bug #1179
    	    	push @{$xcp_request->{attributes}->{nameserver_list}},
			{ name =>$in{$key}, sortorder => $sortorder };

		$sortorder++;
	    }
	    next;
	}

        #
        # Add the nexus data if it's defined
        #
    	if ( $key eq 'app_purpose' ||
             $key =~ /^nexus_/ ) {
	    if  ( defined $in{$key} ) {
                my $xcp_key = $key;
                $xcp_key =~ s/^nexus_//;
                $xcp_request->{attributes}->{tld_data}->{nexus}->{$xcp_key} = $in{$key};
	    }
	    next;
	}

        #
        # Add the CED contact info if it's defined...
        #
    	if ( $key =~ /^ced_/ ) {
	    if  ( defined $in{$key} ) {
                my $xcp_key = $key;
                $xcp_key =~ s/^ced_//;
                $xcp_request->{attributes}->{tld_data}->{ced_info}->{$xcp_key} = $in{$key};
	    }
	    next;
	}
        
        if ( $key eq 'forwarding_email' ) {
            $xcp_request->{attributes}->{tld_data}->{forwarding_email} = $in{$key};
            next;
        }

	$xcp_request->{attributes}->{$key} = $in{$key};
    }

    #
    # Get a list of the domains and stick them into the list. This PUNY
    # converts the name which in turn gets set off to the registrar.
    my @domains;
    foreach (split /\0/, $in{domain})
    {
	$domain = $_;
	$domain = native_to_puny($domain, \%OPENSRS);
        push (@domains, $domain);
    }

    # if multiple domains are being registered based on a new profile,
    # send the necessary flag down to the server so they stay under the
    # same profile
    if (scalar @domains > 1 and not $xcp_request->{attributes}->{reg_domain}) {
	$link_domains = 1;
    }

    if($xcp_request->{attributes}->{reg_domain}){
    	$xcp_request->{attributes}->{reg_domain} = 
	    native_to_puny($xcp_request->{attributes}->{reg_domain}, \%OPENSRS);
    }

    # tell the server whether or not we should override the reseller's
    # default tech contact info and nameserver info
    $xcp_request->{attributes}->{custom_tech_contact} = $REG_SYSTEM{custom_tech_contact};
    if ($in{reg_type} eq 'new' and $REG_SYSTEM{custom_nameservers}) {
	$xcp_request->{attributes}->{custom_nameservers} = 1;
    } else {
	$xcp_request->{attributes}->{custom_nameservers} = 0;
    }

    # add auto_renew option
    $xcp_request->{attributes}{auto_renew} = $in{auto_renew};
    
    # add whois_privacy option
    $xcp_request->{attributes}{f_whois_privacy} = $in{f_whois_privacy};
    
    # attempt to register the domains one at a time...
    my $count = 1;
    my $queued_count = 0;

    foreach $domain (@domains) {
	$xcp_request->{attributes}->{encoding_type} = $in{language_tag};
	
        # Undo the punycode for display purposes.
        #
        $punycodeObj	= puny_to_native($domain, \%OPENSRS);
        $revDomain	= sprintf("%s" , $punycodeObj);

    	# need to set the actio and object to lower case because
	# send_cmd() transforms them up.
	$xcp_request->{action} = lc $xcp_request->{action};
    	$xcp_request->{object} = lc $xcp_request->{object};

	$xcp_request->{attributes}->{domain} = $domain;

	# if this is the first of several domains based on a new profile
	# tell the server that this domain should be the primary domain for
	# the group of domains being processed
	if ($count == 1 and $link_domains) {
	    $xcp_request->{attributes}->{link_domains} = 1;
	} else {
	    $xcp_request->{attributes}->{link_domains} = 0;
	}

	# register the domain
	$register_results = $XML_Client->send_cmd( $xcp_request );
    
	if ($register_results->{is_success}) {
	
	    $id = $register_results->{attributes}->{id};

	    # if this is the first of several domains based on a new profile
	    # set its id as master_order_id so that when the other domains
	    # are inserted they are linked against the primary domain
	    if ($count == 1 and $link_domains) {
		$xcp_request->{attributes}->{master_order_id} = $id;
	    }
	    # only increment the count for successful orders
	    $count++;

            #
            # KLUDGE ALERT!!!!!!!!
            # Perl, for some reason, hacks and coughs on high-8 chars when performing an
            # append to a string. We perform the sprintf to avoid it. Change this and the
            # MLDN which appears on the screen will not be the one the user is requesting.
            # 
            my $x = sprintf ("<BR>%s processed with order # %d. %s.\n", $revDomain, $id, $register_results->{response_text} );
            $status .= $x;

	    ############################################################
	    # sample routine to send message to admin with billing info
	    
	    if ($REG_SYSTEM{F_SEND_ORDERS}) {
		if ($in{reg_type} eq 'new') {
		    $reg_type = "New Domain";
		} else {
		    $reg_type = "Transfer";
		}

		# .ca doesn't have owner email; use admin instead.
		if ( $in{ domain } =~ /\.ca$/i ) {
		    $in{ owner_email } ||= $in{ admin_email };
		}

                #
	        # sample routine to send message to customer
                # THINK: Email
		send_email("$path_templates/message.txt",
			  {
			   %in,
			   domain =>  $domain,
			   mailfrom => $in{owner_email}||$ADMIN_EMAIL,
			   mailto => $ADMIN_EMAIL,
			   id => $id,
			   period_text => $REG_PERIODS{$in{period}},
			   reg_type => $reg_type,
			   });
	    }
	    

            #
	    # sample routine to send message to customer
            # THINK: Email
	    if (not ( $in{reg_type} eq 'transfer' and 
		      $in{domain} =~ /\.ca/ )
		){
		if ($REG_SYSTEM{F_SEND_THANKYOU}) {
		    if ($in{domain} =~ /\.ca$/){
			$in{owner_first_name}||=$in{admin_first_name};
			$in{owner_email}||=$in{admin_email};
		    }
		    send_email("$path_templates/thankyou.txt",
			       {
				   %in,
				   domain =>  $domain,
				   mailto => $in{owner_email},
				   mailfrom => $ADMIN_EMAIL,
				   id => $id,
			       });
		}
	    }
	    ################################################################
	
	} elsif ( $F_QUEUE_SUPPLIER_UNAVAILABLE and
		  $register_results->{attributes}->{queue_request_id}){
	    #xxx Request has been queued and we don't have a order here?
	    # what should we do??? WE have only queue_request_id which will
	    # be deleted once request processed. In most of the cased order 
	    # will be created, but if data is realy-realy 
	    # bad then order won't be created
	    #
            $status .= sprintf ("Domain: [%s] registration request has been placed in a registrar's queue.<br>\n", $revDomain);
	    $queued_count++;

	} else {
            #
            # KLUDGE ALERT!!!!!!!!
            # Perl, for some reason, hacks and coughs on high-8 chars when performing an
            # append to a string. We perform the sprintf to avoid it. Change this and the
            # MLDN which appears on the screen will not be the one the user is requesting.
            #
            my $x = sprintf ("Domain: %s Registration attempt failed: %s. <br>", $revDomain, $register_results->{response_text});
            $status .= $x;
	
	    if ($register_results->{attributes}->{error}) {
		$register_results->{attributes}->{error} =~ s/\n/<br>\n/g;
		$status .= " $register_results->{attributes}->{error}";
		if ( $register_results->{response_code} == 486 )
		{
		    $status .= '&nbsp;&nbsp;&nbsp; Please retry in a minute or two.<BR>';
		}
	    }
	    
	    $status .= "<br>\n";
	}
    }

    $HTML{status} = $status;
    $HTML{partner_email} = $ADMIN_EMAIL;
    $HTML{CGI} = $cgi;
    $HTML{affiliate_id} = $in{affiliate_id};

    print_form("$path_templates/thankyou.html",\%HTML);
}


sub do_bulk_transfer {
    my (%HTML,%data,@params,$order_ids,$order_errors);
    my ($domain,$status,$id,$xcp_request);
    my @domains = split /\0/, $in{domain};

    $xcp_request = {
	action => "bulk_transfer",
	object => "domain",
	attributes => {
#Uncomment one of the string or pass a specific value of parameter
#If not passed or value not save|process then settings from RSP profile will be used
#		    handle => 'save',  #save order only regardless RSP settings
#		    handle => 'process', #process order always regardless RSP settings 
	    domain_list => \@domains,
	},
    };

    if ( $in{ mldn } ) {
	$xcp_request->{attributes}{encoding_type} = $OPENSRS{IDN_ENCODING_TYPE};
    }
    my $key;
	
    if (defined $in{flag_admin_use_contact_info} and 
	$in{flag_admin_use_contact_info}) {
	foreach $key (keys %in) {
	    if ($key =~ /^admin_(.+)$/) {
		$in{"admin_$1"} = $in{"owner_$1"};
	    }
	}
    }

    if (defined $in{flag_billing_use_contact_info} and 
	$in{flag_billing_use_contact_info}) {
	foreach $key (keys %in) {
	    if ($key =~ /^billing_(.+)$/) {
		$in{"billing_$1"} = $in{"owner_$1"};
	    }
	}
    } elsif (defined $in{flag_billing_use_admin_info} and 
	     $in{flag_billing_use_admin_info}){
	foreach $key (keys %in) {
	    if ($key =~ /^billing_(.+)$/) {
		$in{"billing_$1"} = $in{"admin_$1"};
	    }
	}
    }
	
    # clean up data that was posted, stick it in %data
    foreach my $key (keys %in) {
	$in{$key} = unencode($in{$key});
    }
    
    
    # clean up data that was posted, stick it in %data
    foreach my $key (keys %in) {
	
	next if $key eq "domain";
	
    	if ( $key =~ /^(owner|billing|tech|admin)_/i )	{
	    my $contact_type = $1;
	    my $contact_key = $key;
	    $contact_key =~ s/^(owner|billing|tech|admin)_//i;
	    if  ( exists $contact_keys{$contact_key} )	    {
    	    	$xcp_request->{attributes}->{contact_set}->{$contact_type}->{$contact_key} =
		    $in{$key};
	    }
	    next;
	}
    	
	$xcp_request->{attributes}->{$key} = $in{$key};
    }

    # tell the server whether or not we should override the reseller's
    # default tech contact info and nameserver info
    $xcp_request->{attributes}->{custom_tech_contact} = $REG_SYSTEM{custom_tech_contact};
    $xcp_request->{attributes}->{custom_nameservers} = 0;

    my $register_results = $XML_Client->send_cmd( $xcp_request );

    # get the results for the entire transaction
    if ($register_results->{is_success}) {
	
	# get the results for each domain
	
	$status = $register_results->{response_text}."<BR><BR>";
	$status .= "Batch transfer order #".
	    	    $register_results->{attributes}->{bulk_transfer_id}.
		    "<BR>"; 
	foreach my $key ( @{$register_results->{attributes}->{successful_domains}}) {
	    my $domain = $key->{domain};
	    my $order_id = $key->{order_id};
	    
	    $status .= "$domain processed with order # $order_id.<br>\n";
	    $order_ids .= "$domain processed: order # $order_id\n";
	    
	}
	
	foreach my $key ( @{$register_results->{attributes}->{failure_domains}}) {
	    my $domain = $key->{domain};
	    my $reason = $key->{reason};
	    
	    $status .= "Unable to process transfer request for $domain: $reason<br>\n";
	    $order_errors .= "$domain failed: $reason\n";
	    
	}
	
	############################################################
	# sample routine to send message to admin with billing info
	
	if ($REG_SYSTEM{F_SEND_ORDERS}) {
	    send_email("$path_templates/bulk_transfer_message.txt",
		       {
			%in,
			bulk_transfer_id => $register_results->{attributes}->{bulk_transfer_id},
			mailfrom => $in{owner_email},
			mailto => $ADMIN_EMAIL,
			order_ids => $order_ids,
			order_errors => $order_errors,
		       });
	}
	
	# sample routine to send message to customer
	if ($REG_SYSTEM{F_SEND_THANKYOU}) {
	    send_email("$path_templates/bulk_transfer_thankyou.txt",
		       {
			%in,
			bulk_transfer_id => $register_results->{attributes}->{bulk_transfer_id},
			mailto => $in{owner_email},
			mailfrom => $ADMIN_EMAIL,
			order_ids => $order_ids,
		       });
	}
	
    } else {
	
	$status .= "Batch transfer attempt failed.<br><br>\n";
	$status .= "<menu>$register_results->{response_text}<br>\n";
	
	if ($register_results->{attributes}->{error}) {
	    $register_results->{attributes}->{error} =~ s/\n/<br>\n/g;
	    $status .= " $register_results->{attributes}->{error}";
	    if ( $register_results->{response_code} == 486 )
	    {
		$status .= '&nbsp;&nbsp;&nbsp; Please retry in a minute or two';
	    }
	}
	$status .= "</menu>\n";
	
	$status .= <<EOF;
<br><br>
If you would like to retry the order please hit your browser\'s 'Back' button
and re-submit the request.
EOF
	error_out($status);
	exit;
	
    }

    $HTML{status} = $status;
    $HTML{partner_email} = $ADMIN_EMAIL;
    $HTML{CGI} = $cgi;
    $HTML{affiliate_id} = $in{affiliate_id};
    $HTML{bulk_transfer_id} = $register_results->{bulk_transfer_id};
    print_form("$path_templates/bulk_transfer_thankyou.html",\%HTML);

}

###############################################################
###############################################################
### the rest of the subroutines should not need modification
###############################################################
###############################################################

sub lookup {
    
    my (%HTML,$status,$match_string,$matches);
    my ($xcp_request,$lookup_results,$match,$error_msg);
    my ($matchRef);
    
    my $domain		= native_to_puny(trim($in{domain}), \%OPENSRS);
    my $affiliate_id	= $in{affiliate_id};
    
    $xcp_request = {
    	    	action => "lookup",
		object => "domain",
		attributes => {
		    domain => $domain,
		    affiliate_id => $affiliate_id,
		    },
		};

    
    $lookup_results = $XML_Client->send_cmd( $xcp_request );
    if ($lookup_results->{is_success} or 
	$F_QUEUE_SUPPLIER_UNAVAILABLE ) {
	
	$status = $lookup_results->{attributes}->{status};
	if ( $status eq 'available' or 
	     (	$F_QUEUE_SUPPLIER_UNAVAILABLE and 
		$status eq 'invalid' and 
		$lookup_results->{attributes}->{noservice}
	     )) {
	    
	    $matches = $lookup_results->{attributes}->{matches}||[];
	    $match_string = <<EOF;
<center>
<input type=checkbox name=domain value="$domain" checked> $domain&nbsp;&nbsp;
EOF
	    my $counter = 1;

	    #check tld_related lookup statuses for noservice
	    #if queueing enabled
	    if ( $F_QUEUE_SUPPLIER_UNAVAILABLE or
		 defined $lookup_results->{attributes}{lookup}){
		my %domain_hash = (); 
		@domain_hash{@$matches} = ();
		my $lookup_results  =  $lookup_results->{attributes}{lookup};
		foreach my $dom (keys %$lookup_results){
		    next if exists $domain_hash{$dom};
		    if ( not ($lookup_results->{$dom}{status} eq 'invalid' 
			      and $lookup_results->{$dom}{noservice})) {
			next;
		    }
		    $domain_hash{$dom} = undef;
		}
		$matches = [keys %domain_hash];
	    }
	    foreach $match (@$matches) {
		if ( $counter >= 3 )
		{
		    $match_string .= "<BR>";
		    $counter = 0;
		}

                #
                # Undo the punycode for display purposes.
                #
                $match = puny_to_native($match, \%OPENSRS);

		$match_string .= <<EOF;
<input type=checkbox name=domain value="$match"> $match&nbsp;&nbsp;
EOF
	    	$counter++;
	    }
	    if ($domain =~ /\.name$/ and
		    ($lookup_results->{attributes}->{email_available} == 1 or
			$F_QUEUE_SUPPLIER_UNAVAILABLE and
			$lookup_results->{attributes}->{noservice})
		) {
	   	my $email = $domain;
		$email =~ s/\./@/;
		$match_string .= "<P>The related e-mail address $email is also available.<BR>Would you like to purchase it together with the domain?<BR>\n";
		$match_string .= <<EOF;
<input type="radio" name="email_bundle" value="1" checked>Yes&nbsp;&nbsp;<input type="radio" name="email_bundle" value="0">No
EOF
	    }
	    $match_string .= "</center>\n";

	    $HTML{matches}	= $match_string;
	    $HTML{domain}	= $domain;
	    $HTML{CGI}		= $cgi;
	    $HTML{OrderCGI}     = $cgi;
	    $HTML{method}	= 'POST';
	    $HTML{affiliate_id}	= $in{affiliate_id};
	    if  ($lookup_results->{response_code} == 246) { #blocker
		$HTML{notes}='Domain names of other level exist.';
	    }
	    elsif ($lookup_results->{response_code} == 247){ #municipal
		$HTML{notes}='Domain name is restricted to municipal government';
	    }
		
		 

            #createMLDNSHTMLLink (\%HTML);

	    my ( $tld ) = $domain =~ m/$OPENSRS_TLDS_REGEX$/i;
	    if ( exists $REG_SYSTEM{ post_lookup }{ $tld } ) {
		my $hr = $REG_SYSTEM{ post_lookup }{ $tld };
    
		no strict 'refs';
		&{$hr->{sub}}(\%HTML, $hr, $lookup_results);
		use strict;
	    }

	    print_form("$path_templates/avail.html",\%HTML);
	    
	} elsif ($status eq 'invalid') {
	    if ( $lookup_results->{response_code} == 436 ) {
	       my $error_msg = $lookup_results->{response_text};
	       error_out($error_msg);
	       exit;
	    } else {
	       my $error_msg = "Your domain name: $domain was in an invalid format.\n";
	       error_out($error_msg);
	       exit;
	    }
	} elsif ($status eq 'taken') {


            if ($domain =~ /\.name$/) {
	   	my $email = $domain;
		$email =~ s/\./@/;
		$HTML{matches} .= "<P>The domain or the related e-mail address $email has already been purchased by another ".
                                  "registrant.<br>We recommend you try a different .name domain in order to take ".
                                  "advantage of the email forward feature.<BR><BR>\n";
            }
            
            # domain was taken
	    $matches = $lookup_results->{attributes}->{matches};

	    # only show order button if there were other available matches
	    if ( $matches ) {
		$match_string = "<b>The following similar domains are available:</b> <br><br><center>\n";
    	    	my $tempCounter = 0;
		foreach $match (@$matches) {
		    if ( $tempCounter >= 3 )
		    {
		    	$match_string .= "<BR>";
			$tempCounter = 0;
		    }
                $match = puny_to_native($match, \%OPENSRS);
		    $match_string .= <<EOF;
<input type=checkbox name=domain value="$match"> $match&nbsp;&nbsp;
EOF
		    $tempCounter++;
		}
		$match_string .= "</center>\n";

		$HTML{matches} .= <<EOF;
<FORM method="post" ACTION="$cgi" >
<input type=hidden name=affiliate_id value="$in{affiliate_id}">
<input type=hidden name=action value="setup_profile">

<TABLE  BORDER=0 CELLPADDING=0>
<TR><TD>
$match_string
<BR>
</TD>
</TR>

<TR><TD>
<CENTER>
<HR SIZE=1 width=80%>
</CENTER>

Proceed to the order form by clicking on the button below<BR>
or skip to the bottom of the page to check on another name.
<BR>
</TD></TR>

<TR><TD ALIGN=center valign=bottom colspan=3>
<INPUT TYPE="submit" VALUE="Reserve Now!">
</TD></TR></TABLE>
</FORM>
EOF

	    }

	    $HTML{domain}	= puny_to_native($domain, \%OPENSRS);
	    $HTML{CGI}		= $cgi;
	    $HTML{affiliate_id}	= $in{affiliate_id};

            #createMLDNSHTMLLink (\%HTML);

	    print_form("$path_templates/taken.html",\%HTML);
	    

    	} else {
	    $error_msg = $lookup_results->{response_text};
	    error_out($error_msg);
	}
	
    } else {
	$error_msg = $lookup_results->{response_text};
	error_out($error_msg);
	exit;
    }
    
}


sub get_price {
    my ($domain) = @_;

    my $xcp_request = {
	action => 'get_price',
        object => 'domain',
        attributes => {
            domain => $domain,
            period => 1,
        }
    };

    my $price_results = $XML_Client->send_cmd( $xcp_request );
    return $price_results->{attributes}{price};
}

sub check_transfer {

    my ($xcp_request,$domain_string,%HTML,$error_msg);

    my $domain = $in{domain};
    my $affiliate_id = $in{affiliate_id};

    my $puny_domain	= native_to_puny($domain, \%OPENSRS);
    $xcp_request = {
	action	    => "check_transfer",
	object	    => "domain",
	attributes  => {
	    affiliate_id    => $affiliate_id,
	    domain => $puny_domain,
	},
    };

    my $transfer_check = $XML_Client->send_cmd( $xcp_request );
    if ($transfer_check->{is_success}) {
	if ( $transfer_check->{attributes}->{transferrable} == 1 or
	     $transfer_check->{attributes}->{noservice} and
             $F_QUEUE_SUPPLIER_UNAVAILABLE
	   ) {
	    $domain_string = "<input type=hidden name=domain value=\"$domain\">\n";

	    $HTML{domain_string} = $domain_string;
	    $HTML{CGI} = $cgi;
	    $HTML{affiliate_id} = $affiliate_id;
	    $HTML{reg_type} = "transfer";
	    $HTML{bulk_order} = 0; # eg, not bulk
	    $HTML{title} = "Domain Transfer for $domain";
	    print_form("$path_templates/setup_profile.html",\%HTML);
	} else {
	    error_out("The domain $domain is not currently transferable:  $transfer_check->{attributes}->{reason}.\n");
	    exit;
	}
    } else {
	$error_msg = $transfer_check->{response_text};
	error_out($error_msg);
	exit;
    }

}

sub setup_profile {
    
    my (%HTML,$domain,$domain_string,$must_match);
 
    my @domains = split /\0/, $in{domain};
    if (not @domains) {
	error_out("You need to select at least one domain to register.\n");
	exit;
    }

    foreach $domain (@domains) {
	$domain_string .= "<input type=hidden name=domain value=\"$domain\">\n";
    }

    $HTML{domain_string} = $domain_string;
    if ($domains[0] =~ /\.name$/) {
	if ($in{email_bundle}) {
		$HTML{email_bundle} = "<INPUT TYPE=\"hidden\" NAME=\"email_bundle\" VALUE=1>";
	}
    } 
    $HTML{CGI} = $cgi;
    $HTML{affiliate_id} = $in{affiliate_id};
    $HTML{reg_type} = "new";

    if ( $in{must_match_profile} )
    {
    	$must_match = "_must_match";
	if ( $in{domain} =~ /\.ca/ )
	{
	    $HTML{message} = <<EOF
This .ca domain is restricted and can only be registered if it is linked to an<BR>
an already active .ca domain with the same CIRA registrant.
EOF
	}
	else
	{
	    $HTML{message} = <<EOF
The registration of this domain is conditional on its registration being linked<BR>
with another existing active domain.
EOF
	}
    }
    $HTML{bulk_order} = 0;	# eg, not bulk
    my $domains = join ", ", @domains;
    $HTML{title} = "Domain Registration for $domains";
    print_form("$path_templates/setup_profile${must_match}.html",\%HTML);
}

sub do_setup_profile {

    my (%HTML,$domain,$domain_string,@domains,$domain_info,$punycode,$field,
        $htmlForm,$domainCountry);

    my $reg_username = $in{reg_username};
    my $reg_password = $in{reg_password};
    my $confirm_password = $in{confirm_password};
    my $flag_get_userinfo = $in{flag_get_userinfo};
    my $reg_domain = $in{reg_domain};
    my $tmp_encoding_type;
    my $legal_type='';
    my $syntax_error_msg = "Password syntax is incorrect!<BR> 
        To register domain, please go to manage interface, change password and start registration over.<BR>
	Password may only contain alphanumeric characters and symbols []()!@\$^,.~|=-+_<BR> 
	and have at least 3 and at most 20 characters.<BR>";
    
    if ($reg_username =~ /^\s*$/)
    {
	error_out("Please provide a username.\n");
	exit;
    }
    if ( length($reg_username) > 20) 
    {
	error_out ("Username should be no longer than 20 characters.\n");
	exit;
    }
    if (lc($reg_username) !~ /^[a-z0-9]+$/)
    {
	error_out("Username may only contain alphanumeric characters a-z and 0-9.\n");
	exit;
    }

    #
    # Check the passwords. 
    #
    if ($reg_password ne $confirm_password)
    {
	error_out ("Password mismatch.\n");
	exit;
    }
    if (not $reg_password)
    {
	error_out("Please provide a password.\n");
	exit;
    }
    if (length($reg_password) < 3 || length($reg_password) > 20 || (lc($reg_password) !~ /^[A-Za-z0-9\[\]\(\)!@\$\^,\.~\|=\-\+_\{\}\#]+$/))
    {
	# if it is existing user, let the profiles be retrieved, otherwise just print error and exit.
        if ($flag_get_userinfo) {
	    $HTML{syntax_error_msg} = $syntax_error_msg;
	} else {
	    error_out("Password may only contain alphanumeric characters and symbols []()!@\$^,.~|=-+_{}# and have at least 3 and at most 20 characters\n");
            exit;
	}
    }


    if ( ( $flag_get_userinfo ) &&
	 ( not $reg_domain )
	 ){
	error_out("Please provide a domain's profile to retrieve.\n");
	exit;
    }

    #bulk .ca must be on the previous profile only
    if ( $in{bulk_order} and 
	 $in{domain_country} eq 'ca' and 
	 $reg_domain  !~/ca$/i and
	 $in{reg_type} eq 'new') {
	error_out("Please provide a .ca domain's profile to retrieve.\n");
	exit;
    }

    if ($flag_get_userinfo) {
	# base registration on existing profile
	# get profile based on domain/username/password
	my $xcp_request = {
			action => "get",
			object => "domain",
			attributes => {
			    type => "all_info",
			    affiliate_id => $in{affiliate_id},
			    reg_username => $reg_username,
			    reg_password => $reg_password,
			    domain => native_to_puny($reg_domain, \%OPENSRS),
			}
		       };
    
	$HTML{reg_profile} = "Based on $reg_domain/$reg_username";
	if ($reg_domain  =~/ca$/i){
	    $HTML{reg_profile}.="<i> - a CIRA registrant profile will be used </i>";
	}
	
	
        #
        # Send the domain lookup off. The PUNY converted name is being sent.
        #
	$domain_info = $XML_Client->send_cmd( $xcp_request );
	if (not $domain_info->{is_success}) {
	    error_out("Failed attempt: $domain_info->{response_text}");
	    exit;
	}
	$legal_type=$domain_info->{attributes}{legal_type} if $domain_info->{attributes}{legal_type};

	# process this through escape() to account for " and ' in the data
        escape_hash_values( $domain_info );
	#%HTML = map { $_, escape($domain_info{$_}) } keys %domain_info;

    	#
	# now have to convert object format into denormalized format
	#
	foreach my $typeKey ( keys %{$domain_info->{attributes}->{contact_set}} ) {
	    foreach my $dataKey ( keys %{$domain_info->{attributes}->{contact_set}->{$typeKey}} ) {
		$HTML{$typeKey."_".$dataKey} =
	    	    $domain_info->{attributes}->{contact_set}->{$typeKey}->{$dataKey};
	    }
	}
	
	delete $domain_info->{attributes}->{contact_set};

	my $fqdnCounter = 1;
	foreach my $nameserver ( @{$domain_info->{attributes}->{nameserver_list}} ) {
	    $HTML{"fqdn".$fqdnCounter} = $nameserver->{name};
	    $fqdnCounter++;
	}

	foreach my $attrKey ( keys %{$domain_info->{attributes}} ) {
	    $HTML{$attrKey} = $domain_info->{attributes}->{$attrKey};
	}

	
	$HTML{reg_domain} = $reg_domain;
	if ($in{domain} =~ /eu$/){
	    $HTML{country_menu} = build_eu_countries_list($HTML{owner_country});
	} else {
	    $HTML{country_menu} = locale_build_country_list($HTML{owner_country});
	}
	#build select box for the EU/BE language of  correspondence	
	if ($in{domain} =~ /eu$/){
	    $HTML{eu_languages} = build_eu_languages_list($HTML{owner_lang});
	}
	if ($in{domain} =~ /be$/){
	    $HTML{be_languages} = build_be_languages_list($HTML{owner_lang});
	}
				    
	
	$HTML{billing_country_menu} =locale_build_country_list($HTML{billing_country});
	$HTML{admin_country_menu} = locale_build_country_list($HTML{admin_country});


	$HTML{"CATEGORY_" . $domain_info->{attributes}->{nexus}->{category}} = "checked";
	$HTML{APP_PURPOSE_LIST} = build_app_purpose_list( $domain_info->{attributes}->{nexus}->{app_purpose} );
	$HTML{CITIZEN_COUNTRY_LIST} = locale_build_country_list( $domain_info->{attributes}->{nexus}->{validator} ?
                                                          $domain_info->{attributes}->{nexus}->{validator} : '--');

        # Build .ASIA select options list for display in HTML templates...
        $HTML{CED_CONTACT_TYPE_LIST}=build_ced_contact_type_select_list($domain_info->{attributes}->{ced_info}->{contact_type});
        $HTML{CED_LOCALITY_COUNTRY_LIST}=build_ced_locality_select_list($domain_info->{attributes}->{ced_info}->{locality_country});
        $HTML{CED_LEGAL_ENTITY_TYPE_LIST}=build_ced_entity_type_select_list($domain_info->{attributes}->{ced_info}->{legal_entity_type});
        $HTML{CED_ID_TYPE_LIST}=build_ced_entity_type_select_list($domain_info->{attributes}->{ced_info}->{id_type});

    } else {
	# make a new profile
	$HTML{reg_profile} = "New";
    
	if ($in{domain} =~ /eu$/i){
	    $HTML{country_menu} = build_eu_countries_list();
	} else {
	    $HTML{country_menu} = locale_build_country_list();
	}
        #build select box for the EU/BE language of  correspondence
	if ($in{domain} =~ /eu$/){
	    $HTML{eu_languages} = build_eu_languages_list($HTML{owner_lang});
	}
	if ($in{domain} =~ /be$/){
	    $HTML{be_languages} = build_be_languages_list($HTML{owner_lang});
	}
	$HTML{billing_country_menu} = $HTML{country_menu};
	$HTML{admin_country_menu} = $HTML{country_menu};
    }

    if ( $in{bulk_order} and 
	 $in{domain_country} eq 'ca'
	 or $in{domain} =~ /\.ca\b/){
	$HTML{ca_domains} = 1;
    }

    $HTML{CGI} = $cgi;
    $HTML{reg_username} = $reg_username;
    $HTML{reg_password} = $reg_password;
    $HTML{affiliate_id} = $in{affiliate_id};
    $HTML{reg_type} = $in{reg_type};
    $HTML{bulk_order} = $in{bulk_order};
    $HTML{CC_YEARS} = build_select_menu(get_cc_years(),(localtime)[5] + 1900);
    $HTML{domain} = $in{domain}; 
    if ($REG_SYSTEM{custom_tech_contact}) {
	$HTML{CUSTOM_TECH_CONTACT} = build_tech_contact(\%HTML);
    }

    # nameserver information is only relevant for new domains
    if ($in{reg_type} eq 'new' and $REG_SYSTEM{custom_nameservers}) {
	$HTML{CUSTOM_NAMESERVERS} = build_nameservers(\%HTML);
    }
    
   if ( $MANAGE{allow_domain_locking} and not $in{bulk_order} and $in{domain} =~ /$OPENSRS{ TLDS_SUPPORTING_LOCKING }/ ) {
	    $HTML{LOCK_DOMAIN} = <<EOF;
<tr>
<td align=right bgcolor="#e0e0e0"><b>Lock Domain</b></td>
<td>
<input type=radio name=f_lock_domain value=1> Yes
<input type=radio name=f_lock_domain value=0 checked> No
</td>
</tr>
EOF
    }

    if ($in{reg_type} eq 'new') {
	# new domains
	$HTML{reg_text} = 'Registration';
	$HTML{reg_type_text} = 'New Domain';
	if ($in{bulk_order}) {
	    $HTML{heading} = 'Batch Domain Registration';
            $HTML{PERIOD_LIST} = build_select_menu(\%REG_PERIODS,1);
	} elsif ( $in{domain} &&
	          $in{domain} =~ /uk$/i ) {
	    $HTML{PERIOD_LIST} = build_select_menu(\%UK_REG_PERIODS,2);
	}elsif ( $in{domain} &&
                  $in{domain} =~ /name$/i ) {
            $HTML{PERIOD_LIST} = build_select_menu(\%NAME_REG_PERIODS,1);
	} elsif ( $in{domain} &&
	          $in{domain} =~ /(de|eu|be)$/i ) {
	    $HTML{PERIOD_LIST} = build_select_menu(\%DE_REG_PERIODS,1);
	} else {
	    $HTML{PERIOD_LIST} = build_select_menu(\%REG_PERIODS,1);
	}
	my $allow_locking = $MANAGE{ allow_domain_locking };

	$allow_locking &= $in{domain} =~ /$OPENSRS{ TLDS_SUPPORTING_LOCKING }/;
	if ( $allow_locking ) {
	    $HTML{ LOCK_DOMAIN } = <<EOF;
<tr>
<td align=right bgcolor="#e0e0e0"><b>Lock Domain</b></td>
<td>
<input type=radio name=f_lock_domain value=1> Yes
<input type=radio name=f_lock_domain value=0 checked> No
</td>
</tr>
EOF
	}
    } else {
	# transfer
	if ($in{bulk_order}) {
	    $HTML{reg_type_text} = 'Batch Transfer';
	    $HTML{heading} = 'Batch Transfer';
	} else {
	    $HTML{reg_type_text} = 'Transfer';
	}
	$HTML{reg_text} = 'Transfer';
	if ( $in{domain} =~ /\.uk$/ ) {
	    $HTML{PERIOD_LIST} = build_select_menu(\%UK_REG_PERIODS,2); 
	} else {
	    $HTML{PERIOD_LIST} = build_select_menu(\%TRANSFER_PERIODS);
	}
    }
    
    

    if ( ( $in{domain} &&
	   $in{domain} =~ /\.ca/i ) ||
	 ( $in{domain_country} &&
	   $in{domain_country} eq 'ca' ) )
    {
    	$domainCountry = "_ca";
	$HTML{country_menu} = locale_build_country_list($HTML{owner_country}||'CA');
	$HTML{billing_country_menu} = locale_build_country_list($HTML{billing_country}||'CA');



	$HTML{domain_country} = $in{domain_country};
	$HTML{ca_legal_type_menu} = build_ca_domain_legal_types($legal_type);
    }
    elsif ( ( $in{domain} &&
	      $in{domain} =~ /\.us/i ) ||
	    ( $in{domain_country} &&
	      $in{domain_country} eq 'us' ) ) {
    	$domainCountry = "_us";
	$HTML{country_menu} = locale_build_country_list($HTML{owner_country}||'US');
	$HTML{billing_country_menu} = locale_build_country_list($HTML{billing_country}||'US');
	$HTML{domain_country} = $in{domain_country};
        $HTML{CITIZEN_COUNTRY_LIST} = locale_build_country_list('--') if not exists $HTML{CITIZEN_COUNTRY_LIST};
        $HTML{APP_PURPOSE_LIST} = build_app_purpose_list() if not exists $HTML{APP_PURPOSE_LIST};
    }
    elsif ( ( $in{domain} &&
	      $in{domain} =~ /\.asia/i ) ||
	    ( $in{domain_country} &&
	      $in{domain_country} eq 'asia' ) ) {
    	$domainCountry = "_asia";
	$HTML{domain_country} = $in{domain_country};

        # Build .ASIA select options list for display in HTML templates...
        $HTML{CED_CONTACT_TYPE_LIST}=build_ced_contact_type_select_list($HTML{ced_contact_type});
        $HTML{CED_LOCALITY_COUNTRY_LIST}=build_ced_locality_select_list($HTML{ced_locality_country});
        $HTML{CED_LEGAL_ENTITY_TYPE_LIST}=build_ced_entity_type_select_list($HTML{ced_legal_entity_type});
        $HTML{CED_ID_TYPE_LIST}=build_ced_identification_type_select_list($HTML{ced_id_type});
    }
    elsif ( ( $in{domain} &&
	      $in{domain} =~ /\.name/i && $in{email_bundle} == 1) ||
            ( $in{domain_country} &&
              $in{domain_country} eq 'name' ) ) {
    	    $domainCountry = "_name";
	    $HTML{domain_country} = $in{domain_country};
    }
    elsif ( ( $in{domain} &&
              $in{domain} =~ /\.de/i) ||
            ( $in{domain_country} &&
              $in{domain_country} eq 'de' ) ) {
            $domainCountry = "_de";
            $HTML{domain_country} = $in{domain_country};
    }
    elsif ( ( $in{domain} &&
              $in{domain} =~ /\.eu/i) ||
            ( $in{domain_country} &&
              $in{domain_country} eq 'eu' ) ) {
            $domainCountry = "_eu";
            $HTML{domain_country} = $in{domain_country};
    }
    elsif ( ( $in{domain} &&
              $in{domain} =~ /\.be/i) ||
            ( $in{domain_country} &&
              $in{domain_country} eq 'be' ) ) {
            $domainCountry = "_be";
            $HTML{domain_country} = $in{domain_country};
    } else {
    	$domainCountry = "";
    }

    my ($tld) = $in{domain} =~ /$OPENSRS_TLDS_REGEX$/i;
    if ( ( $tld &&
           $RENEW{capability}->{$tld} &&
           $REG_SYSTEM{allow_auto_renew} ) || 
         ( $in{bulk_order} && $REG_SYSTEM{allow_auto_renew} ) )
    {
    	$HTML{AUTO_RENEW} = <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#e0e0e0"><B>Auto renew:</B><BR>
	<font color=red>
	********ATTENTION********<BR>
	A payment system must be implemented before
	giving your customers access to turn auto renew
	on for a new domain.
        </font>
	</TD>
	<TD><INPUT NAME="auto_renew" TYPE="radio" value="1"> Yes 
		<INPUT NAME="auto_renew" TYPE="radio" value="0" CHECKED> No </TD>
</TR>
EOF
    }
    
    $HTML{WHOIS_PRIVACY} = <<EOF;
<tr>
<td align=right bgcolor="#e0e0e0"><b>WHOIS Privacy:</b><br><br>
WHOIS Privacy is applicable for .com, .net, .org, .biz, .cc, 
.tv, .info, and .asia domains.<br><br>
WHOIS Privacy expiration date remains open for a domain 
that is set to auto-renew.<br><br>
When the domain is not set to auto renew, 
the WHOIS Privacy expiration date is set 
to the domain's expiration date.
</td>
<td>
<input type=radio name=f_whois_privacy value="1"> Yes
<input type=radio name=f_whois_privacy value="0" checked> No
</td>
</tr>
EOF
    
    if ( $F_SHOW_CC_FIELDS ) {
       $HTML{CC_FIELDS} = get_content("$path_templates/cc_fields.html",
            {
                CC_YEARS => build_select_menu(get_cc_years(),(localtime)[5] + 1900)
            });
    }
    
    if ($in{bulk_order}) {
	$htmlForm = "$path_templates/bulk_order$domainCountry.html";
	if ( $in{reg_type} eq 'transfer' and $in{domain_country} eq 'ca'){
	    $htmlForm = "$path_templates/transfer_ca.html";
	    $HTML{domains}="<textarea name=domains cols=20 rows=5></textarea>";
	} elsif ($in{reg_type} eq 'transfer') {
    	    $htmlForm = "$path_templates/bulk_transfer.html";
	}
    } else {
	@domains = split /\0/, $in{domain};
	foreach $domain (@domains) {
	    $domain_string .= "<input type=hidden name=domain value=\"$domain\">\n";
	    if ( $in{reg_type} eq 'new' and 
		 not $HTML{LANGUAGE_LIST} and 
		 native_to_puny($domain, \%OPENSRS) =~ /xn--.+\.(?:com|net|de|org|biz|cc|tv|info)/ ) {
	        my $language_list = OpenSRS::Language::build_universal_encoding_menu( Domain => $domain );
	        $HTML{LANGUAGE_LIST} = <<EOF;
<TR>
	<TD bgcolor="#e0e0e0" align=right><B>Language for IDN domain:</B></td>
	<TD><select name=language_tag>$language_list</select></TD>
</TR>
EOF
	    }
	}
	$HTML{domain_string} = $domain_string;
	$HTML{domains} = join "<br>\n", @domains;
	if ( $in{reg_type} eq 'transfer' and
	     $in{domain} =~ /\.ca\b/) {
	    $htmlForm = "$path_templates/transfer_ca.html";
	} elsif ($in{reg_type} eq 'transfer' and
		 $in{domain} =~ /\.de$/) {
	    $htmlForm = "$path_templates/transfer_de.html";
	} elsif (  $in{reg_type} eq 'transfer' and
		   $in{domain} =~ /\.uk$/ ) {
		    $htmlForm = "$path_templates/transfer_uk.html";
	} else {
            if ($in{reg_type} ne 'transfer') {
                $HTML{reg_period_hints} = get_content("$path_templates/reg_period_hints.html");    
            }
	    $htmlForm = "$path_templates/order$domainCountry.html";
	}
    }
    print_form($htmlForm,\%HTML);
}# end of do_setup_profile

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

sub error_out {
    
    my (%HTML);
    $HTML{CGI} = $cgi;
    $HTML{ERROR} = shift;
    print_form("$path_templates/error.html",\%HTML);
    
}

##########################################################################
# substitute values on the specified template and print it to the client

# an optional 'type' arg can be passed: 'framed' specifies to pull in base.html
# as the outer frame and the given template as the inner frame
# 'single' specifies to use the given template alone
# the default behavior is 'framed'
sub print_form {
    
    my ($type,$content);

    my @args = @_;
    my ($template,$HTML) = @args[0,1];
    if ($args[2]) { $type = $args[2] }
    else { $type = 'framed' }

    #if (not $HTML->{REG_ENCODING_TYPE_LIST})
    #{
    #    my $etypes;
    #    foreach my $key13 (keys %MLDNS)
    #    {
    #            $etypes .="<OPTION VALUE=\"" . $key13 . "\">" . $MLDNS{$key13} . "\n";
    #    }
    #    $HTML->{REG_ENCODING_TYPE_LIST} = $etypes;
    #}

    if ($type eq 'framed') {
	$HTML->{CONTENT} = get_content("$template",$HTML);
    
	open (FILE, "<$path_templates/base.html") or die "Couldn't open $path_templates/base.html: $!\n";
	while (<FILE>) {
	    s/{{(.*?)}}/pack('A*',$HTML->{$1})/eg;
	    $content .= $_;
	}
	close FILE;
    } else {
	open (FILE, "<$template") or die "Couldn't open $template: $!\n";
	while (<FILE>) {
	    s/{{(.*?)}}/pack('A*',$HTML->{$1})/eg;
	    $content .= $_;
	}
	close FILE;
    }
    print $content;
}

####################################################
# grab the contents of a template, substitute any supplied values, and return
# the results
sub get_content {
    
    my $content;
    
    my ($template,$HTML) = @_;
    open (FILE, "<$template") or die "Couldn't open $template: $!\n";
    while (<FILE>) {
	s/{{(.*?)}}/pack('A*',$HTML->{$1})/eg;
	$content .= $_;
    } 
    close FILE;
    
    return $content;
    
}

###########################################################
#### sample routines for ordering domains in bulk

sub bulk_order {

    my $title = "Batch Domain Registration";
    my %HTML = (
		CGI => $cgi,
		affiliate_id => $in{affiliate_id},
		domain_country => lc( $in{domain_country} ),
		reg_type => 'new',
		bulk_order => 1,
		title => $title,
		);
    print_form("$path_templates/setup_profile.html",\%HTML);
}

sub bulk_order_ca {

    my %HTML = (
		CGI => $cgi,
		affiliate_id => $in{affiliate_id},
		domain_country => "ca",
		reg_type => 'new',
		bulk_order => 1,
		title => 'Batch Domain Registration',
		);
    print_form("$path_templates/setup_profile_ca.html",\%HTML);
}

sub bulk_order_us {

    my %HTML = (
		CGI => $cgi,
		affiliate_id => $in{affiliate_id},
		domain_country => "us",
		reg_type => 'new',
		bulk_order => 1,
		title => 'Batch Domain Registration',
		);
    print_form("$path_templates/setup_profile.html",\%HTML);
}

sub bulk_order_asia {

    my %HTML = (
		CGI => $cgi,
		affiliate_id => $in{affiliate_id},
		domain_country => "asia",
		reg_type => 'new',
		bulk_order => 1,
		title => 'Batch Domain Registration',
		);
    print_form("$path_templates/setup_profile.html",\%HTML);
}

sub bulk_transfer {

    my %HTML = (
		CGI => $cgi,
		affiliate_id => $in{affiliate_id},
		reg_type => 'transfer',
		bulk_order => 1,
		title => 'Batch Domain Transfer',
		);
    if ($in{tld} eq '.ca'){
	$HTML{domain_country}='ca';
    }
    print_form("$path_templates/setup_profile.html",\%HTML);
}

############################################################

sub get_cc_years {

    my (%years,$i);
    my $year = (localtime)[5];
    $year += 1900;

    for ($i = 0; $i <=5; $i++) {
	$years{$year} = $year;
	$year++;
    }

    return \%years;

}

sub cc_verify {
    my ($number) = @_;
    my ($i, $sum, $weight);

    return 0 if $number =~ /[^\d\s\-]/;

    $number =~ s/\D//g;

    return 0 unless length($number) >= 13 && 0+$number;

    for ($i = 0; $i < length($number) - 1; $i++) {
    $weight = substr($number, -1 * ($i + 2), 1) * (2 - ($i % 2));
    $sum += (($weight < 10) ? $weight : ($weight - 9));
    }

    return 1 if substr($number, -1) == (10 - $sum % 10) % 10;
    return 0;
}

sub cc_exp_verify {

    my ($cc_exp_mon,$cc_exp_yr) = @_;

    my ($month,$year) = (localtime)[4,5];
    $month++;
    $year += 1900;

    my $current_month = sprintf("%04d%02d",$year,$month);
    my $cc_exp = sprintf("%04d%02d",$cc_exp_yr,$cc_exp_mon);
    if ($current_month > $cc_exp) {
	return 0;
    }
    return 1;
}

sub build_tech_contact {
    
    my $data = shift;
    if ( $data->{ca_domains}  and $data->{bulk_order}) {
	#pass all information as a hidden fields
	#we don't need it in general - CIRA informatino will stay the same
	#but we have to provide them to by pass our order own validation
	my @list = qw (tech_org_name tech_first_name tech_last_name
		       tech_city tech_address1 tech_state tech_country
		       tech_phone tech_fax tech_email tech_postal_code
		       ); 
	my $html=<<EOF;
	    <TR><TD COLSPAN=2 ALIGN=right>
NOTE: The Technical Contact for these domains will be the Technical
Contact listed for the domain $data->{reg_domain} at CIRA. This information will be displayed for confirmation purposes on a subsequent page.
</TD></TR>
EOF
	
	map {
	    $html.=qq/<input type="hidden" name="$_" value="$data->{$_}">\n/;
	} @list;
	return $html;
    }

    my $tech_country_menu = locale_build_country_list($data->{tech_country});
    my $tech_corr_lang;
    if ($data->{domain} =~ /eu$/){
	$tech_corr_lang = build_eu_languages_list($data->{tech_lang});
    }
    if ($data->{domain} =~ /be$/){
	$tech_corr_lang = build_be_languages_list($data->{tech_lang});
    }
		    
    my $tech_address = <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Street Address:</B></TD>
	<TD><input name="tech_address1" size=39 value="$data->{tech_address1}"></TD>
</TR>
EOF
    my $tech_use_billing_info=<<EOF;
		<B>Same as Billing Information</B>
<input type=checkbox name="flag_tech_use_billing_info" value="1">
EOF
    my $tech_use_contact_info=<<EOF;
		<B>Same as Owner Information</B>
<input type=checkbox name="flag_tech_use_contact_info" value="1"><br>
EOF
    my $tech_use_admin_info=<<EOF;
        <B>Same as Admin Information</B>
<input type=checkbox name="flag_tech_use_admin_info" value="1"><br>
EOF
    my $if_more_than_one = <<EOF;
<br><font color=red size=-1>If more than one checkbox is selected, 'Owner Information' has precedence over 'Admin Information', and 'Admin Information' has precedence over 'Billing Information'.</font>
EOF
    if ( not $data->{ca_domains} ) {
	$tech_address .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
		*optional*</font> <B>(eg: Suite #245):</B></TD>
	<TD><input name="tech_address2" size=39 value="$data->{tech_address2}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
		*optional*</font> <B>Address 3:</B></TD>
	<TD><input name="tech_address3" size=39 value="$data->{tech_address3}"></TD>
</TR>
EOF
	if ($data->{domain} =~ /(eu|be)$/){
	    $tech_use_billing_info = '';
	    $tech_use_admin_info = '';
	    $if_more_than_one = '';
	}
    } else {
	$tech_use_billing_info = '';
	$tech_use_contact_info = '';
	$if_more_than_one = '';
    }

    my $fax_option = $in{ domain } =~ /\.de$/ ? "" : "*optional*";
    my $html = <<EOF;
<TR>
	<TD COLSPAN=2 bgcolor="#90c0ff" align=center>
		<B><FONT SIZE=+1>Tech Contact Information</FONT></B>
	</TD>
</TR>
<TR>
	<TD COLSPAN=2 bgcolor="#e0e0e0" align=center>
$tech_use_contact_info
$tech_use_admin_info
$tech_use_billing_info
$if_more_than_one
	</TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>First Name:</B></TD>
	<TD><input name="tech_first_name" size=15 value="$data->{tech_first_name}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Last Name:</B></TD>
	<TD><input name="tech_last_name" size=15 value="$data->{tech_last_name}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Organization Name:</B></TD>
	<TD><input name="tech_org_name" size=39 value="$data->{tech_org_name}"></TD>
</TR>
$tech_address
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>City:</B></TD>
	<TD><input name="tech_city" size=15 value="$data->{tech_city}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>State:</B></TD>
	<TD><input name="tech_state" size=15 value="$data->{tech_state}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Country:</B></TD>
	<TD>
	    <SELECT NAME="tech_country">
$tech_country_menu
	    </SELECT>
	</TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Postal Code:</B></TD>
	<TD><input name="tech_postal_code" size=15 value="$data->{tech_postal_code}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Phone Number:</B></TD>
	<TD><input name="tech_phone" size=40 value="$data->{tech_phone}"> 
		<br><font size=-1> (eg. +1.4165551122)*</font>
		</TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
		$fax_option</font> <B>Fax Number:</B>
	</TD>
	<TD><input name="tech_fax" size=40 value="$data->{tech_fax}"></TD>
</TR>
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Email:</B><BR>
	    <FONT color=red size=-1>Must be currently valid address</FONT>
	</TD>
	<TD><input name="tech_email" size=39 value="$data->{tech_email}"></TD>
</TR>
EOF
    if ($data->{domain} =~ /(eu|be)$/){
	$html .= <<EOF;
<TR>
    <TD ALIGN=right bgcolor="#90c0ff">
	<font color=red size=-1>*optional*</font>
	<B>VAT Registration Number::</B><BR>
    </TD>
    <TD><input name="tech_vat" size=39 value="$data->{tech_vat}"></TD>
</TR>
<TR>
    <TD ALIGN=right bgcolor="#90c0ff"><B>Language of Correspondence:</B></TD>
    <TD><SELECT NAME="tech_lang">
$tech_corr_lang
    </SELECT></TD>
</TR>
EOF
    }
   return $html;					     
}

sub build_tech_verify {

    my $data = shift;
    
    my $tech_address2 = $data->{tech_address2};
    my $tech_address3 = $data->{tech_address3};
    my ($tech_vat,$tech_lang);
    if ($data->{domain} =~ /(eu|be)$/) {
	$tech_vat= "vat: $data->{tech_vat}<br>\n";
	$tech_lang = "language: $data->{tech_lang}<br>\n";
    }
    if ($tech_address2) { $tech_address2 .= "<br>\n" }
    if ($tech_address3) { $tech_address3 .= "<br>\n" }
    my $html = <<EOF;
<tr><td colspan=2 align=center><b>Tech Contact Information</b></td></tr>

<tr>
<td valign=top>
$data->{tech_first_name} $data->{tech_last_name}<BR>
$data->{tech_org_name}<BR>
$data->{tech_address1}<BR>
$tech_address2
$tech_address3
$data->{tech_city}, $data->{tech_state} $data->{tech_postal_code}<BR>
$data->{tech_country}<BR>
</td>
<td valign=top>
Phone:$data->{tech_phone}<BR>
Fax:$data->{tech_fax}<BR>
E-mail:$data->{tech_email}<BR>
$tech_vat
$tech_lang
</td>
</tr>
EOF
    return $html;
}

sub build_nameservers {

    my (%fqdns,%nameservers,$key,$num,$fqdn_punycode_obj);

    my $data = shift;
    foreach $key (grep /^fqdn\d+$/, keys %$data) {

	($num) = $key =~ m/^fqdn(\d+)$/;
	$fqdns{$num} = $data->{$key};
    }

    my $count = 1;
    foreach $num (sort keys %fqdns) {
	$nameservers{"fqdn$count"} = $fqdns{$num};
	$count++;
    }

    #
    # We need to get a list of available 
    #
	

    my $html = <<EOF;
<TR>
	<TD COLSPAN=2 bgcolor="#90c0ff" align=center>
		<B><FONT SIZE=+1>DNS Information</FONT></B>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Primary DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn1" size=39 value="$nameservers{fqdn1}"><BR>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><B>Secondary DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn2" size=39 value="$nameservers{fqdn2}"><BR>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
                *optional*</font> <B>Third DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn3" size=39 value="$nameservers{fqdn3}"><BR>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
                *optional*</font> <B>Fourth DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn4" size=39 value="$nameservers{fqdn4}"><BR>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
                *optional*</font> <B>Fifth DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn5" size=39 value="$nameservers{fqdn5}"><BR>
	</TD>
</TR>
EOF
    $html .= <<EOF;
<TR>
	<TD ALIGN=right bgcolor="#90c0ff"><font color=red size=-1>
                *optional*</font> <B>Sixth DNS Hostname:</B></TD>
	<TD>
	    <input name="fqdn6" size=39 value="$nameservers{fqdn6}"><BR>
	</TD>
</TR>
EOF

    return $html;
}
