#!/usr/local/bin/perl

#       .Copyright (C)  1999-2002 TUCOWS.com Inc.
#       .Created:       11/19/1999
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Originally Developed by:
#                       Tucows/OpenSRS
#       .Authors:       Evgeniy Pirogov
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

# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
use vars qw/$path_to_config $q $session %in $path_templates $error/;
BEGIN {
      $path_to_config = '/home/westcoas/opensrs-client-3.0.0/etc';
      do "$path_to_config/OpenSRS.conf";
}
use lib $PATH_LIB;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use strict;
use CGI qw();

use HTML::Template;
use Core::Exception;
use OpenSRS::XML_Client;
use OpenSRS::Util::Common qw/locale_build_country_list build_select_menu CODE_2_Country send_email/;
use OpenSRS::Util::Error;
use OpenSRS::Util::Canada qw/@municipal_prefix legal_type_list %canada_legal_types %legal_types %lang_pref %legal_type_groups help_icon %canada_province/;
use OpenSRS::Util::Logger '$Log';# => "$PATH_LOG/ca_reg.txt", qw/info error debug/; 
use OpenSRS::Util::Logger '$Billing';# => "$PATH_LOG/billing_ca.txt", qw/info/; 
use OpenSRS::Util::Session; 
use Data::Dumper;

use constant CC_TYPES => {
    visa => "Visa",
    mastercard => "Mastercard",
    amex => "American Express",
    discover => "Discover",
};

use constant ACTION_MAP => {
    show_lookup => \&show_lookup,
    lookup => \&lookup,
    blocker_ok => \&blocker_ok,
    legal_type_quiz => \&legal_type_quiz,
    legal_type_quiz2 => \&legal_type_quiz2,
    verify_legal_type => \&verify_legal_type,
    setup_contact => \&setup_contact,
    setup_contact2 => \&setup_contact2,
    setup_profile => \&setup_profile,
    create_new_profile => \&create_new_profile,
    link_osrs_profile => \&link_osrs_profile,
    how_to_link_ca => \&how_to_link_ca,
    link_ca_domain => \&link_ca_domain,
    link_ca_domain2 => \&link_ca_domain2,
    verify_order => \&verify_order,
    submit_order => \&submit_order,
    help	 => \&help,
    help_icon => \&help_icon,
};

$q = new CGI;
try {
    %in = $q->Vars;
    undef $error;
    $session = OpenSRS::Util::Session->restore(
	    $in{session},
	    $in{sign},
	    $OPENSRS{private_key});

    $Log->debug('restored session %s', Dumper($session));
    $session->{history} = [] unless ref $session->{history} eq 'ARRAY';  
    delete $in{session};
    delete $in{sign};
    $Log->debug('got from web %s', Dumper(\%in));

    $path_templates = "$PATH_TEMPLATES/ca_reg"; 
    local $ENV{HTML_TEMPLATE_ROOT} = "$PATH_TEMPLATES/ca_reg"; 
    my $action = $in{action};
    delete $in{action};

    my $back = $in{back}||0;
    delete $in{back};
    if ($back){
	$Log->debug('back buton pressed');
	shift @{$session->{history}};
	my $state = shift @{$session->{history}};
	if ($state) {
	    $action = $state->{action};
	    %in = %{$state->{in}}; 
	} else {
	    $action = '';
	    $in{affiliate_id} = $session->{affiliate_id};
	}
     
    }

    $action ||= 'show_lookup';
    $Log->debug('try to process action %s with %s', $action, Dumper(\%in));


    unless (ACTION_MAP->{$action}){
	throw 'web',"Invalid Action '%s'",$action;	
    }

    my ($template,@ret_data) = &{ACTION_MAP->{$action}}();

    if (defined $error){
	my $state = ${$session->{history}}[0];
	my %error_in = (%in); 
	if ($state){
	    $action = $state->{action};
	    %in = %{$state->{in}};
	} else {
	    $action = 'show_lookup';
	    $in{affiliate_id} = $session->{affiliate_id};
	} 
	($template,@ret_data) = &{ACTION_MAP->{$action}}();
	push @ret_data,%error_in,%$error;
    } else {
	unshift @{$session->{history}},{action => $action, in=>{%in}};
    }


    my %data = (cgi => $q->url,@ret_data) ;

    if ($template) {
	    $template = HTML::Template->new(
		    filename => $template, 
		    die_on_bad_params => 0);
	    $template->param(%data);
	    $template->param($session->dump($OPENSRS{private_key}));
#	    if ($REG_SYSTEM{debug}){
#		$template->param(dumper => scalar Dumper(\%data,$session));
#	    }
	    print $q->header;
	    print $template->output;
    }
} catch {
    dev => sub {
	my $E = shift;
	$Log->fatal("dev error %s",$E->dump);
	print $q->header;
	error_output($E->info);
    },
    _other => sub {
	my $E = shift;
	$Log->error("other %s",$E->dump);
	print $q->header;
	error_output();
    },
};

exit;

sub show_lookup {
    $session->{history} = [];
    return 'lookup.html', 
	    municipality_list => [ map { {prefix=>$_} } @municipal_prefix],
	    @_;
}

sub lookup {
    $session->{affiliate_id} = $in{affiliate_id};
    my $client = new OpenSRS::XML_Client( %OPENSRS,
					  lookup_all_tlds => 0);
    $client->login;
    #do lookup and see
    my @parts = ();
    push @parts => $in{prefix} if $in{prefix};
    push @parts => $in{root};
    push @parts => $in{suffix};
      
    my $domain = join (".",@parts);
    $session->add( domain => $domain);
    $session->add( prefix => $in{prefix});

    my $response = $client->send_cmd({
			action => 'lookup',
			object => 'domain',
			attributes => {
			    domain => $domain,
			    affiliate_id => $in{affiliate_id}
			}
		    });

    $Log->debug('Got this lookup %s',Dumper($response));

    #problem with is_success and noserice
    #has to check for noservice before is_success
    if ( $response->{attributes}{status} eq 'invalid' and
	 $response->{attributes}{noservice} and 
	 $F_QUEUE_SUPPLIER_UNAVAILABLE) {

	#it may be blocker or municipal - we don't know here because of outage
	#let's pray it will be regular domain without addinional headache
	#if you don't want to deal with .ca when CIRA is out - 
	#just comment out following return
	$session->add(
		      ca_reg_type => 'regular',
		     );
        return 'new_ca_domain.html', 
		    domain => $session->{domain},
		    period => $session->{period},
		    linked => $session->{linked},
		    allow_auto_renew => $REG_SYSTEM{allow_auto_renew},
		    auto_renew => $session->{auto_renew},
		    isa_trademark => $session->{isa_trademark};
    }


    #error
    unless ($response->{is_success} or $F_QUEUE_SUPPLIER_UNAVAILABLE ){
	throw 'comm','Communication error %s',Dumper($response);
    }

    if ($response->{attributes}{status} eq 'available'){
	#available
	if ($response->{response_code} == 247){
	    #municipal
	    $session->add(
		      ca_reg_type => 'municipal',
	    );
	    return 'new_municipal_domain.html', 
			domain => $session->{domain},
			period => $session->{period},
			linked => $session->{linked},
			auto_renew => $session->{auto_renew},
			allow_auto_renew => $REG_SYSTEM{allow_auto_renew};
	} elsif ($response->{response_code} == 246){
	    #blocker
	    my $blockers = $client->send_cmd({
                        action => 'get_ca_blocker_list',
                        object => 'domain',
                        attributes => {
                            domain => $domain,
                        }
            });
	    $Log->debug('Blocker list %s',Dumper($blockers));
	    my @blockers = ();
	    if ( $blockers->{is_success} and
		 ref $blockers->{attributes}{blocker_list} eq 'HASH'){
		    @blockers = map {{name => $_ }} keys %{$blockers->{attributes}{blocker_list}};
	    }
	    return 'blocked_domain.html',
		    domain => $domain, 
		    blockers => \@blockers;
	} else {
	    #regular domain;
	    $session->add(
			  ca_reg_type => 'regular',
			 );
	    return 'new_ca_domain.html', 
			domain => $session->{domain},
			period => $session->{period},
			linked => $session->{linked},
			allow_auto_renew => $REG_SYSTEM{allow_auto_renew},
			auto_renew => $session->{auto_renew},
			isa_trademark => $session->{isa_trademark};
	}
    }
    #invalid
    $error->{error} = $response->{response_text};
}

sub blocker_ok{
    if ($in{has_permission} =~ /yes/i){
	$session->add(ca_reg_type => 'blocker');
        return 'new_ca_domain.html', 
		    domain => $session->{domain},
		    period => $session->{period},
		    linked => $session->{linked},
		    allow_auto_renew => $REG_SYSTEM{allow_auto_renew},
		    auto_renew => $session->{auto_renew},
		    isa_trademark => $session->{isa_trademark};
    }
    return show_lookup( error => qq/
Sorry,<br>
You may not register this domain unless you are able<br>
to obtain permission from the owner(s) of the<br>
blocking domain(s)<br>
/);
}

sub legal_type_quiz {
    $session->add(period => $in{period});
    $session->add(isa_trademark => $in{isa_trademark});
    $session->add(linked => $in{linked});
    $session->add(auto_renew => $REG_SYSTEM{allow_auto_renew} && $in{auto_renew});

    unless ($in{period}){
	$error->{error} = q/Invalid period specified/;
	$error->{error_period} = 1;
	return; 
    }

    if ($in{linked}){
	return how_to_link_ca();
    }

    if ($session->{ca_reg_type} eq 'municipal'){
	my %legal_type_group = legal_type_list('government');
	return 'government_org_name.html',
	    reg_name => $session->{reg_name},
	    reg_desc => $session->{reg_desc},
	    legal_type_list => $legal_type_group{list};
    }

    return 'legal_type_questionnaire.html', $session->{legal_t}.'_legal_t' => 1;
}
 
sub legal_type_quiz2 {
    unless ($in{legal_t}){
	$error->{error} = qq/You haven't selected legal type group/;
	return; 
    }

    if ($in{legal_t} ne $session->{legal_t}){
	$session->add(legal_type => undef);
    }
    $session->add(legal_t => $in{legal_t});

    my %legal_type_group = legal_type_list($in{legal_t});
    my $Choose_Legal_Type = $legal_type_group{'choose_legal_type'} || 'Choose Legal Type';
    my $legal_type_list = $legal_type_group{'list'};

    return 'choose_legal_type.html',
		Choose_Legal_Type => $Choose_Legal_Type,
		legal_type_list => $legal_type_list,
		legal_type => $session->{legal_type},
		long => $canada_legal_types{$session->{legal_type}},
		reg_name => $session->{reg_name},
		reg_desc => $session->{reg_desc},
		legal_t  => $in{legal_t}, 
		intro => $legal_type_groups{$in{legal_t}}{intro};
}

sub verify_legal_type {
    $in{reg_name} =~ s/^\s+//;
    $in{reg_name} =~ s/\s+$//;
    $in{reg_desc} =~ s/^\s+//;
    $in{reg_desc} =~ s/\s+$//;
    $session->add(reg_name => $in{reg_name});
    $session->add(reg_desc => $in{reg_desc});
    $session->add(legal_type => $in{legal_type});
    my %error;
    
    if ($in{reg_name} eq ''){
	$error{error} = "Registrant name can't be empty";
	$error{error_reg_name} = 1;
    }
    if (!exists $canada_legal_types{$in{legal_type}}){
	$error{error} .= "<br>\nYou haven't specified legal type";
	$error{error_legal_type} = 1;
    }

    if (keys %error){
	$error = \%error;
	return;
    }
    
    return 'verify_reg_name.html',
	    reg_name => $in{reg_name},
	    legal_t => $session->{legal_t},
	    %{$legal_types{$in{legal_type}}}; 
    
}

sub setup_contact {
    $in{reg_name} =~ s/^\s+//;
    $in{reg_name} =~ s/\s+$//;
    $session->add(reg_name => $in{reg_name});
    $session->add(data_source => 'manual') unless $session->{data_source};
    if ($in{reg_name} eq ''){
	$error->{error} = "Registrant name can't be empty";
	$error->{error_reg_name} = 1;
	return; 
    }
    return 'ret_domain_info.html',
	    source_domain => $session->{source_domain},
	    source_username => $session->{source_username},
	    source_password => $session->{souce_password},
	    "data_source_".$session->{data_source} => 1;    

}

sub get_info_from_osrs {
    my ($domain,$username,$password) = @_;
    my $client = new OpenSRS::XML_Client( %OPENSRS);
    $client->login;
    my $response = $client->send_cmd({
		    action => "get",
		    object => "domain",
		    attributes => {
			type => "all_info",
			reg_username => $username,
			reg_password => $password,
			domain => $domain,
		    }
		   });

    $Log->debug('got from opensrs %s',Dumper($response));

    if (not $response->{is_success}) {
	return (is_success => 0, error => "Failed attempt: ".
				 $response->{response_text});
    }
    my %hash = (is_success => 1, reg_name => $response->{attributes}{contact_set}{owner}{org_name});
    
    foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax email/){
	$hash{"admin_$field"}  = $response->{attributes}{contact_set}{admin}{$field};
	$hash{"tech_$field"}  = $response->{attributes}{contact_set}{tech}{$field};
    } 
    my $fqdnCounter = 1;
    foreach my $nameserver ( @{$response->{attributes}{nameserver_list}}) {
	$hash{"fqdn$fqdnCounter"} = $nameserver->{name};
	$fqdnCounter++;
    }

    if ($domain =~ /\.ca/){
	$hash{'legal_type'} = $response->{attributes}{legal_type};
	$hash{'cira_member'} = ($response->{attributes}{member} eq 'Y'?1:0);
	$hash{'reg_desc'} = $response->{attributes}{domain_description};
	$hash{'reg_name'} = $response->{attributes}{contact_set}{owner}{org_name};
	$hash{"admin_pref_language"}  = $response->{attributes}{contact_set}{admin}{lang_pref};
	$hash{"tech_pref_language"}  = $response->{attributes}{contact_set}{tech}{lang_pref};
    }
    
    return %hash;
}


sub setup_contact2{
    my %HTML = (custom_dns => $REG_SYSTEM{custom_nameservers}, 
		custom_tech => $REG_SYSTEM{custom_tech_contact});

    $session->add(data_source => $in{data_source});

    if ($in{data_source} eq 'domain'){
	#retreive info from OpenSRS
	unless ($in{source_domain} and
		$in{source_username} and
		$in{source_password}){
	    $error->{error} = 'Domain, username and password are required to retreive information ';
	    $error->{error_source_domain} = !$in{source_domain};
	    $error->{error_source_username} = !$in{source_username};
	    $error->{error_source_password} = !$in{source_password};
	    return;
	}
	$session->add(source_domain => $in{source_domain});
	$session->add(source_username => $in{source_username});
	$session->add(source_password => $in{source_password});

	my %data  = get_info_from_osrs( $in{source_domain},
				     $in{source_username},
				     $in{source_password});
	unless ($data{is_success}){
	    $error->{error} =  $data{error};
	    return;
	}

	foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax pref_language email/){
	    $HTML{"admin_$field"} = $data{"admin_$field"};
	} 

	if ($REG_SYSTEM{custom_tech_contact}){
	    foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax pref_language email/){
		$HTML{"tech_$field"} = $data{"tech_$field"};
	    } 
	}

	if ($REG_SYSTEM{custom_nameservers}){
	    foreach my $i (1..6){
		$HTML{"fqdn$i"} = $data{"fqdn$i"};
	    }
	}
    }

    $HTML{tech_country_list} = locale_build_country_list($session->{tech_country}||$HTML{tech_country}||'CA');

    $HTML{admin_country_list} = locale_build_country_list($session->{admin_country}||$HTML{admin_country}||'CA');
    $HTML{tech_pref_language} ||= 'EN';
    $HTML{admin_pref_language} ||= 'EN';

    $HTML{tech_lang_long} = $lang_pref{ $session->{tech_pref_language}||
					$HTML{tech_pref_language}||'EN'};
    $HTML{admin_lang_long} = $lang_pref{$session->{admin_pref_language}||
					$HTML{admin_pref_language}||'EN'};

    return 'domain_info.html',%HTML,%$session;
}

sub setup_profile {
    $session->add(existing_profile => $in{existing_profile});
    $session->add(rant_no => 0);	#not existing CIRA's profile
    $session->add(ca_link_domain => 0); #not linked to CIRA's profile of 
					#existing .ca opensrs domain
    $session->add(cira_member => $in{cira_member});
    $session->add(tec_as_admin => $in{tec_as_admin});
    my %error = (error => '');

    #save contact info into session
    #save dns info into session

    foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax pref_language email/){
        $session->add("admin_$field" => $in{"admin_$field"});
	if ($REG_SYSTEM{custom_tech_contact}){
		if ($in{tec_as_admin}){
		    $session->add("tech_$field" => $in{"admin_$field"});
		} else {
		    $session->add("tech_$field" => $in{"tech_$field"});
		}
	}
    }

    if ($REG_SYSTEM{custom_nameservers}){
        my $webfqdnCounter = 1;
        my $fqdnCounter = 1;
	while ($webfqdnCounter <= 6){
	    if ($in{"fqdn$webfqdnCounter"}){
		$session->add("fqdn$fqdnCounter" => $in{"fqdn$webfqdnCounter"});
		$fqdnCounter++;
	    }
	    $webfqdnCounter++;
	}
    }

    #now check contact and DNS
    if ($REG_SYSTEM{custom_nameservers}){
	unless ($session->{'fqdn1'}){
	    $error{error} .= 'First DNS is mandatory parameter<br>';
	    $error{error_fqdn1} = 1;
	}
	unless ($session->{'fqdn2'}){
	    $error{error} .= 'Second DNS is mandatory parameter<br>';
	    $error{error_fqdn2} = 1;
	}
    }
    #now check admin
    unless ($session->{admin_first_name}){
	$error{error} .= 'Admin First name is mandatory parameter<br>';
	$error{error_admin_first_name} = 1;
    }
    unless ($session->{admin_last_name}){
	$error{error} .= 'Admin Last name is mandatory parameter<br>';
	$error{error_admin_last_name} = 1;
    }
    unless ($session->{admin_pref_language}){
	$error{error} .= 'Admin Preferred Language is mandatory parameter<br>';
	$error{error_admin_pref_language} =1;
    }
    unless ($session->{admin_org_name}){    
	$error{error} .= 'Admin Organization name is mandatory parameter<br>';
	$error{error_admin_org_name} = 1;
    }
    unless ($session->{admin_address1}){
	$error{error} .= 'Admin Street address is mandatory parameter<br>';
	$error{error_admin_address1} = 1;
    }
    unless ($session->{admin_city}){
	$error{error} .= 'Admin City is mandatory parameter<br>';
	$error{error_admin_city} = 1;
    }
    unless ($session->{admin_state}){
	$error{error} .= 'Admin Province is mandatory parameter<br>';
	$error{error_admin_state} = 1;
    }
    unless ($session->{admin_country}){
	$error{error} .= 'Admin Country is mandatory parameter<br>';
	$error{error_admin_country} = 1;
    }
    if ($session->{admin_country} eq 'CA' and
	not exists $canada_province{$session->{admin_state}}){
	$error{error} .= 'Invalid Canadian Province for Admin contact<br>';
	$error{error_admin_state} = 1;
    }
    unless ($session->{admin_postal_code}){
	$error{error} .= 'Admin Postal Code is mandatory parameter<br>';
	$error{error_admin_postal_code} = 1;
    }
    if ($session->{admin_phone}) {
	 unless (OpenSRS::Syntax::PhoneSyntax($session->{"admin_phone"})){
	    $error{error} .= 'Invalid Admin Phone format<br>';
	    $error{error_admin_phone} = 1;
	}
    } else {
	$error{error} .= 'Admin Phone is mandatory parameter<br>' ;
	$error{error_admin_phone} = 1;
    }
    if ($session->{admin_email}) {
	unless (OpenSRS::XML_Client::check_email_syntax($session->{admin_email})){
	    $error{error} .= 'Invalid Admin Email format<br>';
	    $error{error_admin_email} = 1;
	}
    } else {
	$error{error} .= 'Admin Email is mandatory parameter<br>';
	$error{error_admin_email} = 1; 
    }

    #check tech if custom
    if ( $REG_SYSTEM{custom_tech_contact} and 
	 not $in{tec_as_admin}){

	unless ($session->{tech_first_name}){
	    $error{error} .= 'Tech First name is mandatory parameter<br>';
	    $error{error_tech_first_name} = 1;
	}
	unless ($session->{tech_last_name}){
	    $error{error} .= 'Tech Last name is mandatory parameter<br>';
	    $error{error_tech_last_name} = 1;
	}
	unless ($session->{tech_pref_language}){
	    $error{error} .= 'Tech Preferred Language is mandatory parameter<br>';
	    $error{error_tech_pref_language} =1;
	}
	unless ($session->{tech_org_name}){    
	    $error{error} .= 'Tech Organization name is mandatory parameter<br>';
	    $error{error_tech_org_name} = 1;
	}
	unless ($session->{tech_address1}){
	    $error{error} .= 'Tech Street address is mandatory parameter<br>';
	    $error{error_tech_address1} = 1;
	}
	unless ($session->{tech_city}){
	    $error{error} .= 'Tech City is mandatory parameter<br>';
	    $error{error_tech_city} = 1;
	}
	unless ($session->{tech_state}){
	    $error{error} .= 'Tech Province is mandatory parameter<br>';
	    $error{error_tech_state} = 1;
	}
	unless ($session->{tech_country}){
	    $error{error} .= 'Tech Country is mandatory parameter<br>';
	    $error{error_tech_country} = 1;
	}
	if ($session->{tech_country} eq 'CA' and
	    not exists $canada_province{$session->{tech_state}}){
	    $error{error} .= 'Invalid Canadian Province for Tech contact<br>';
	    $error{error_tech_state} = 1;
	}
							    
	unless ($session->{tech_postal_code}){
	    $error{error} .= 'Tech Postal Code is mandatory parameter<br>';
	    $error{error_tech_postal_code} = 1;
	}
	if ($session->{tech_phone}) {
	     unless (OpenSRS::Syntax::PhoneSyntax($session->{"tech_phone"})){
		$error{error} .= 'Invalid Tech Phone format<br>';
		$error{error_tech_phone} = 1;
	    }
	} else {
	    $error{error} .= 'Tech Phone is mandatory parameter<br>' ;
	    $error{error_tech_phone} = 1;
	}
	if ($session->{tech_email}) {
	    unless (OpenSRS::XML_Client::check_email_syntax($session->{tech_email})){
		$error{error} .= 'Invalid Tech Email format<br>';
		$error{error_tech_email} = 1;
	    }
	} else {
	    $error{error} .= 'Admin Tech is mandatory parameter<br>';
	    $error{error_tech_email} = 1; 
	}

    }

    if ($error{error} ){
	$error = \%error; 
	return;
    }

    #now let see what we need to do with profile
    if ($in{existing_profile}){
	return 'link_osrs_profile.html', 
	    reg_username => $session->{reg_username},
	    reg_domain => $session->{reg_domain},
	    reg_password => $session->{reg_password} ;
    } else {
	return 'new_profile.html',
	    reg_username => $session->{reg_username},
	    reg_password => $session->{reg_password} ;
    }
}

sub create_new_profile{
    my %error = (error => ''); 
    if (not $in{reg_username}) {
	$error{error} .= "No username supplied<br>"; 
	$error{error_reg_username} = 1;
    }
    $session->add(reg_username => $in{reg_username});
    if (not $in{reg_password}) {
	$error{error} .= "No password supplied<br>"; 
	$error{error_reg_password} = 1;
    }
    if ($in{reg_password} ne $in{verify_password}){
	$error{error} .= "Password mismatch<br>";
	
    }
    if ($in{reg_password} !~ /^[A-Za-z0-9\[\]\(\)!@\$\^,\.~\|=\-\+_\{\}\#]+$/) {
	$error{error} .= "Invalid password syntax: The only allowed characters are all alphanumerics (A-Z, a-z, 0-9) and symbols []()!@\$^,.~|=-+_{}#<br>";
	$error{error_reg_password} = 1;
    }
    if (length $in{reg_password} < 3 || length $in{reg_password} > 20) {
        $error{error} = "Invalid password length: Password should contain at least 3 and at most 20 characters.<br>";
	$error{error_reg_password} = 1;
    }
    if ($error{error}){
	$error = \%error;
	return;
    }

    $session->add(reg_password => $in{reg_password});
    $session->add(reg_domain => undef);
    if ( $F_SHOW_CC_FIELDS ) {
	return show_payment_info();
    } else {
	return verify_order();
    }

}

sub link_osrs_profile{
    my %error = (error => ''); 
    if (not $in{reg_username}) {
	$error{error} .= "No username supplied<br>"; 
	$error{error_reg_username} = 1;
    }
    $session->add(reg_username => $in{reg_username});

    if (not $in{reg_password}) {
	$error{error} .= "No password supplied<br>"; 
	$error{error_reg_password} = 1;
    }
    $session->add(reg_password => $in{reg_password});

    if (not $in{reg_domain}) {
	$error{error} .= "No Domain name supplied<br>"; 
	$error{error_reg_domain} = 1;
    }
    $session->add(reg_domain => $in{reg_domain});
    
    if ($session->{ca_link_domain} and 
	$in{reg_domain} !~ /\.ca$/){
	$error{error} .= 'Existing domain has to be .ca domain<br>';
	$error{error_reg_domain} = 1;
    }

    if ($error{error}){
	$error = \%error;
	return;
    }

    my $client = new OpenSRS::XML_Client( %OPENSRS);
    $client->login;

    my $response = $client->send_cmd({
                action => "set",
                object => "cookie",
                attributes => {
                    domain => $in{reg_domain},
                    reg_username => $in{reg_username},
                    reg_password => $in{reg_password},
                    }
            });

    $Log->debug('Got from OpenSRS on set cookie %s', Dumper($response));
    if (not $response->{is_success}) {
	$error->{error} = "$response->{response_text}<br>\n";
	return;
    }
    if (not $response->{attributes}->{cookie}){
	$error->{error} = "Invalid username/password given.<br>\n";
	return;
    }

    if ($session->{ca_link_domain}){
        my %data  = get_info_from_osrs( $in{reg_domain},
                                        $in{reg_username},
                                        $in{reg_password});
        unless ($data{is_success}){
            $error->{error} =  $data{error};
            return;
        }

        foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax pref_language email/){
            $session->add("admin_$field" => $data{"admin_$field"});
            $session->add("tech_$field" => $data{"tech_$field"});
        }
        $session->add('legal_type' => $data{legal_type});
        $session->add('cira_member' => $data{cira_member});
        $session->add('reg_desc' => $data{reg_desc});
        $session->add('reg_name' => $data{reg_name});
        $session->add("admin_pref_language" => $data{admin_pref_language});
        $session->add("tech_pref_language" => $data{tech_pref_language});
    }

    if ( $F_SHOW_CC_FIELDS ) {
	return show_payment_info();
    } else {
	return verify_order();
    }
    
}


sub how_to_link_ca {
    return 'how_to_link_to_ca.html',
	    ($session->{link_rant}?(link_to_rant => 1):(link_to_domain => 1));
}

sub link_ca_domain {
    if ($in{link_to} eq 'rant'){
	$session->add(link_rant => 1);     
	$session->add(link_ca_domain => 0);
	return 'cira_rant_profile.html',
		%$session,
		custom_dns =>  $REG_SYSTEM{custom_nameservers};
    }
 
    $session->add(link_rant => 0);     
    $session->add(link_ca_domain => 1);
    $session->add(existing_profile => 1);
    return 'cira_reg_profile.html',
	    %$session,
	    custom_dns =>  $REG_SYSTEM{custom_nameservers};
}

sub link_ca_domain2 {
    my %error = (error => '');

    if ($session->{link_ca_domain}){
	
	$session->add(rant_no => 0);
	$session->add(ca_link_domain => 1);
    } else {
	unless ($in{rant_no}) {
	    $error{error} .= "No Registrant Number supplied<br>"; 
	    $error{error_rant_no} = 1;
	}
	$session->add(rant_no => $in{rant_no});
	$session->add(ca_link_domain => 0);
	#check that registrant exists
	my $client = new OpenSRS::XML_Client( %OPENSRS);
	$client->login;
	my $response = $client->send_cmd({
		    action => "query_registrant",
		    object => "ca",
		    attributes => {
			domain => '.ca', #not gonna work for other TLDs
			rant_no => $in{rant_no},
			}
		});
	unless ($response->{is_success}){
	    $error->{error} .= $response->{response_text}."<br>\n";
	    $error{error_rant_no} = 1;
	} else {
	    my %data = %{$response->{attributes}};
	    $session->add(%data);
	    $session->add(reg_name => $data{owner_org_name});
	    $session->add(admin_pref_language => $data{admin_lang_pref});
	    $session->add(tech_pref_language => $data{tech_lang_pref});
	}
    }


    if ($REG_SYSTEM{custom_nameservers}){
        my $webfqdnCounter = 1;
        my $fqdnCounter = 1;
	while ($webfqdnCounter <= 6){
	    if ($in{"fqdn$webfqdnCounter"}){
		$session->add("fqdn$fqdnCounter" => $in{"fqdn$webfqdnCounter"});
		$fqdnCounter++;
	    }
	    $webfqdnCounter++;
	}
	#now check contact and DNS
	if ($REG_SYSTEM{custom_nameservers}){
	    unless ($session->{'fqdn1'}){
		$error{error} .= 'First DNS is mandatory parameter<br>';
		$error{error_fqdn1} = 1;
	    }
	    unless ($session->{'fqdn2'}){
		$error{error} .= 'Second DNS is mandatory parameter<br>';
		$error{error_fqdn2} = 1;
	    }
	}
    }
    if ($error{error}){
	$error = \%error;
	return;
    }
    if ($session->{ca_link_domain}){
	return link_osrs_profile();
    }

    $session->add(existing_profile => $in{existing_profile});
    #reset contact informatino from session
    # just to show that OSRS don't need it from us 
    foreach my $field (qw/ org_name first_name last_name address1 address2 city country state postal_code phone fax pref_language email/){
	delete $session->{"admin_$_"};
	delete $session->{"tech_$_"};
    }
 

    if ($in{existing_profile}){
	return 'link_osrs_profile.html', 
	    reg_username => $session->{reg_username},
	    reg_domain => $session->{reg_domain},
	    reg_password => $session->{reg_password} ;
    } else {
	return 'new_profile.html',
	    reg_username => $session->{reg_username},
	    reg_password => $session->{reg_password} ;
    }
     
}

sub show_payment_info{
    my %cc_months =  map {$_ = sprintf('%02d',$_); $_ => $_ }  (0..12);
    $cc_months{'00'} = '--';
    my $year = (localtime)[5];
    #Y2K
    $year -= 100;
    my %cc_year = map { sprintf('%02d',$_) => 2000+$_} ($year .. $year+5);
    $year = sprintf('02d%',$year);

    return 'cc_info.html',
	    p_cc_type => $session->{p_cc_type},
	    p_cc_num => $session->{p_cc_num},
	    p_cc_exp_month_list => build_select_menu(\%cc_months,$session->{p_cc_exp_month}||'00'),
	    p_cc_exp_year_list =>  build_select_menu(\%cc_year,$session->{p_cc_exp_year}|| $year);

}

sub verify_order{
    my %error = (error => '');
    if ($REG_SYSTEM{F_VERIFY_CC}) {
	if (not $in{p_cc_type}){
	    $error{error} .= "Invalid credit card type.<br>\n";
	    $error{error_p_cc_type} = 1;
	}
        if (not cc_verify($in{p_cc_num})) {
	    $error{error} .= "Invalid credit card number.<br>\n";
	    $error{error_p_cc_num} = 1 ;
        }
        if (not cc_exp_verify($in{p_cc_exp_month},$in{p_cc_exp_year})) {
	    $error{error} .= "Invalid credit card expiration: $in{p_cc_exp_month}/$in{p_cc_exp_year}.<br>\n";
	    $error{error_p_cc_exp} = 1;
        }
	if ($error{error}){
	    $error = \%error;
	    return;
	}
    }
    $session->add(p_cc_type => $in{p_cc_type});
    $session->add(p_cc_num => $in{p_cc_num});
    $session->add(p_cc_exp_month => $in{p_cc_exp_month});
    $session->add(p_cc_exp_year => $in{p_cc_exp_year});

    return 'verify_order.html',%$session,
    	custom_dns =>  $REG_SYSTEM{custom_nameservers},
    	custom_tech =>  $REG_SYSTEM{custom_tech_contact},
    	admin_country => CODE_2_Country($session->{admin_country}),
    	tech_country => CODE_2_Country($session->{tech_country}),
    	legal_type => $legal_types{$session->{legal_type}}->{long},
    	p_cc_type => CC_TYPES->{$in{p_cc_type}},
	show_cc_fields => $F_SHOW_CC_FIELDS;

}

sub cc_exp_verify {

    my ($cc_exp_mon,$cc_exp_yr) = @_;

    my ($month,$year) = (localtime)[4,5];
    $month++;
    $year += 1900;

    my $current_month = sprintf("%04d%02d",$year,$month);
    my $cc_exp = sprintf("%04d%02d",2000+$cc_exp_yr,$cc_exp_mon);
    if ($current_month > $cc_exp) {
        return 0;
    }
    return 1;
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

sub submit_order {
    #now the game begin
    #prepare xcp_Request
    my $xcp_request = {
	action => 'sw_register',
	object => 'domain',
	attributes => {
	    reg_type => 'new',
	    domain => $session->{domain},
	    auto_renew => ($session->{auto_renew}?1:0),
	    period => $session->{period},
	    affiliate_id => $session->{affiliate_id},
	    reg_username => $session->{reg_username},
	    reg_password => $session->{reg_password},
	    isa_trademark => $session->{isa_trademark},
	    ca_link_domain => $session->{ca_link_domain},
	    rant_no => $session->{rant_no}, #attribute 
					    #if value 0, '', undef or 
					    #not mentioned at all 
					    #then new CIRA profile to be creatd,
					    #otherwise we will try register
					    # domain for that registrant
	    nameserver_list => [],
	    contact_set => {
		owner => {
		    org_name => $session->{reg_name},
		},
		admin => {
		    lang_pref => $session->{admin_pref_language},
		    first_name => $session->{admin_first_name},
		    last_name => $session->{admin_last_name},
		    org_name => $session->{admin_org_name},
		    address1 => $session->{admin_address1},
		    address2 => $session->{admin_address2},
		    city => $session->{admin_city},
		    state => $session->{admin_state},
		    country => $session->{admin_country},
		    postal_code => $session->{admin_postal_code},
		    phone => $session->{admin_phone},
		    fax => $session->{admin_fax},
		    email => $session->{admin_email},
		},
	    },
	    custom_tech_contact => $REG_SYSTEM{custom_tech_contact},
	    custom_nameservers => $REG_SYSTEM{custom_nameservers},	
	}
    };
    if ($session->{reg_domain}) {
	$xcp_request->{attributes}{reg_domain} = $session->{reg_domain};
    }
    if ($session->{rant_no} or $session->{ca_link_domain}){
	#existing CIRA profile, OSRS gets info from cira and put into an order
	$xcp_request->{attributes}{domain_description} = 'Existing CIRA profile';
	$xcp_request->{attributes}{legal_type} = 'CCT';
	$xcp_request->{attributes}{cira_member} = 'Y';
    } else {
	$xcp_request->{attributes}{domain_description} = $session->{reg_desc},
	$xcp_request->{attributes}{legal_type} = $session->{'legal_type'};
	$xcp_request->{attributes}{cira_member} = ($session->{cira_member}?'Y':'N');
    }
    if ($REG_SYSTEM{custom_tech_contact}){
	my $tech_contact = {
		lang_pref => $session->{tech_pref_language},
		first_name => $session->{tech_first_name},
		last_name => $session->{tech_last_name},
		org_name => $session->{tech_org_name},
		address1 => $session->{tech_address1},
		address2 => $session->{tech_address2},
		city => $session->{tech_city},
		state => $session->{tech_state},
		country => $session->{tech_country},
		postal_code => $session->{tech_postal_code},
		phone => $session->{tech_phone},
		fax => $session->{tech_fax},
		email => $session->{tech_email},
	    };
	$xcp_request->{attributes}{contact_set}{tech} = $tech_contact;
    }
    $xcp_request->{attributes}{contact_set}{billing} = $xcp_request->{attributes}{contact_set}{admin}; #cause CIRA doesn't have it, and we need this section just to by-pass opensrs validation 
    if ($REG_SYSTEM{custom_nameservers}) {
	my $sortorder = 1;
	foreach (1..6){
	    next unless $session->{"fqdn$_"};
	    push @{$xcp_request->{attributes}{nameserver_list}},
		    { name => $session->{"fqdn$_"},
		     sortorder=> $sortorder++ };
	}
    }
    $Log->debug('XCP request is prepared %s',Dumper($xcp_request));
    #
    #
    # charge/authorize here
    #
    $Billing->info("CC Type: %s\n CC #: %s\n CC Exp: %s/%s\n Request: %s ",
		$session->{p_cc_type},
		$session->{p_cc_num},
		$session->{p_cc_exp_month},
		$session->{p_cc_exp_year},
		Dumper($xcp_request));
    my $client = new OpenSRS::XML_Client( %OPENSRS);
    $client->login;
    my $response = $client->send_cmd($xcp_request);
    $Log->debug('got from OSRS %s',Dumper($response));
    my $status = '';
    if ($response->{is_success}) { 
	my $id = $response->{attributes}->{id};
	my $admin_email =  $response->{attributes}->{admin_email};
	$session->add(admin_email => $admin_email);
	if ($REG_SYSTEM{F_SEND_ORDERS}) {
	    send_email("$path_templates/message.txt",
		      {
		       %$session,
		       mailfrom => $session->{admin_email}||
				    $ADMIN_EMAIL,
		       mailto => $ADMIN_EMAIL,
		       id => $id,
		       reg_type => 'New Domain',
		       });
	}
	if ($REG_SYSTEM{F_SEND_THANKYOU}) {
	    send_email("$path_templates/thankyou.txt",
		       {
			   %$session,
			   mailto => $session->{admin_email},
			   mailfrom => $ADMIN_EMAIL,
			   id => $id,
		       });
	}
	if ($session->{ca_reg_type} eq 'municipal'){
	    return 'complete_municipal.html',%$session,order_id => $id;
	} 
	return 'complete.html',%$session,order_id => $id;
    } elsif ( $F_QUEUE_SUPPLIER_UNAVAILABLE and
	      $response->{attributes}->{queue_request_id}){ 
	
	return 'complete_queued.html', %$session;

    }
    return 'error.html', error => sprintf ("Domain: %s Registration attempt failed: %s.", $session->{domain}, $response->{response_text}."<br>".$response->{attributes}{error});
}


sub help {
    unless ($in{legal_t}) {
        throw 'web_error' => 'Legal type group must be specififed';
    }
    unless (exists $legal_type_groups{$in{legal_t}}){
        throw 'web_error' => 'Invalid Legal Type group';
    }
    return 'legal_type_help.html', %{$legal_type_groups{$in{legal_t}}};
}


1;
