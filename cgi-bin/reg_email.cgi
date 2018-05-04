#!/usr/local/bin/perl
#       .Copyright (C)  2002 TUCOWS.com Inc.
#       .Created:       2002/07/17
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://email.tucows.com
#       .Authors:       Daniel Manley
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
#
# $Id: reg_email.cgi,v 1.37 2005/09/12 15:54:36 ygumerova Exp $
#
use vars qw(
	    %in $cgi $session $path_templates %actions $action %cc_types $TPP_Client
	    %contact_keys %data %cc_mons @cc_types $path_to_config
	   );
# Null these things out for mod_perl users
( %in, $cgi, $session, $path_templates, %actions, $action, %cc_mons, %cc_types, $TPP_Client,
  %contact_keys, %data, $path_to_config) = ();


# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
   # first "do" the major config file
   $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
   do "$path_to_config/OpenSRS.conf";
   # now load up the config for Email services
   do "$path_to_config/Email.conf";
}

use strict;
use lib $PATH_LIB;
use CGI ':cgi-lib';
use HTML::Template;
use Data::Dumper;

use OpenSRS::TPP_Client;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use OpenSRS::Util::Common qw(send_email build_select_menu build_select_menu3 build_country_list);
use OpenSRS::XML_Client;
use OpenSRS::ResponseConverter;
use OpenSRS::Util::Session;

# global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/reg_email";
%in = ();

# list of valid actions to execute
%actions = (

            show_lookup => undef,
            do_lookup_email => undef,
            do_lookup_email_bulk => undef,
            
            enter_order_data => undef,
            verify_order_data => undef,
            #do_verify_domain => undef,
            verify_user => undef,
            
            retrieve_contact_info => undef,
            verify_contact_data => undef,
            
            register => undef,
            
	    );

%cc_types = (
	     visa => "Visa",
	     mastercard => "Mastercard",
	     amex => "American Express",
	     discover => "Discover",
	    );

@cc_types = ( keys %cc_types );
 
%cc_mons = (1=>"01", 2=>"02", 3=>"03", 4=>"04", 5=>"05", 6=>"06", 7=>"07",
		8=>"08",9=>"09",10=>"10",11=>"11",12=>"12",);


print "Content-type:  text/html\n\n";

# start things up

# set debugging level
start_up();

# create a client object which we will use to connect to the Tucows OpenSRS server
$TPP_Client = new OpenSRS::TPP_Client(
    %OPENSRS,
    response_converter => new OpenSRS::ResponseConverter(),
);
$TPP_Client->login;

# read in the form data
ReadParse(\%in);
delete $in{error_message};

$action = $in{action};

$session = OpenSRS::Util::Session->restore(
               $in{session},
               $in{sign},
               $OPENSRS{private_key});
delete $in{session};
delete $in{sign};
delete $in{action};

#-----------------------------------------------------
# perform necessary actions

# no action was supplied, so use the default
if (not $action) {
    show_lookup();

# they passed a valid action
} elsif (exists $actions{$action}) {
    no strict "refs";
    &$action();
    use strict;

# they passed an invalid action
} else {
    error_out("Invalid action: $action");
}


# close connection to the server
$TPP_Client->logout;

exit;

###########################################################################
sub start_up {

    if ($REG_EMAIL{debug}) {
	#print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
    
    OpenSRS::Util::Common::initialize( path_templates => $PATH_TEMPLATES,
                                       mail_settings => \%MAIL_SETTINGS );
}

sub error_out {
    
    my %HTML = ( ERROR => shift );
    print_form(template => "$path_templates/error.html", data => \%HTML);
    
}

##########################################################################
# substitute values on the specified template and print it to the client

# an optional 'type' arg can be passed: 'framed' specifies to pull in base.html
# as the outer frame and the given template as the inner frame
# 'single' specifies to use the given template alone
# the default behavior is 'framed'
sub print_form {
    my %args = @_;
    
    $args{title} = "E-mail Registration" if not $args{title};
    
    if (0) { #for easy debug test
	local $Data::Dumper::Indent=1;
	local $Data::Dumper::Useqq=0;
	print "<pre>",Dumper(\%args),"</pre>";
    }

    my $template = HTML::Template->new(cache => 1, filename => $args{template}, die_on_bad_params => 0);
    $template->param(CGI=>$cgi,%{$args{data}},$session->dump($OPENSRS{private_key}));
    unless ($args{not_framed}) {
	my $content = $template->output;
	$template = HTML::Template->new(cache => 1, filename => "$path_templates/base.html", die_on_bad_params => 0);
	$template->param(CONTENT=>$content);
    }
    $template->param(CGI=>$cgi,%{$args{data}});
    print $template->output;
}


############################################################
# Credit Card bare-minimum validation

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

# End credit card bare-minimum validation
############################################################

############################################################
# Lookup is the default page to show if no action is 
# specified
sub show_lookup {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );
    
    print_form(template => "$path_templates/lookup.html", data => \%HTML);
}

sub do_lookup_email {

    my %HTML = ( CGI => $cgi, affiliate_id => $in{affiliate_id}, @_ );
    
    my $email_address = $in{email_address};
    my ( $account_name, $email_domain ) = $email_address =~ /(.+)@(.+)/;
    
    if ( ( not $account_name ) || ( not $email_domain ) ) {
        show_lookup(error_message => "Invalid email address.  Try something like 'me\@mydomain.tld'.");
        return;
    }

    # converting our single param into
    # something that the bulk lookup can handle --
    # saves on duplicated code.
    $in{box_names} = $account_name;
    $in{email_domain} = $email_domain;
    
    do_lookup_email_bulk();
}


sub do_lookup_email_bulk {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );

    my $email_domain = $in{email_domain};
    my $box_names = $in{box_names};
    $box_names =~ s/\r//g;
    my @box_names = split /\n/, $box_names;
    my %box_names = ();
    my @account_names = ();

    foreach my $line ( @box_names ) {
        my ($account_name, $real_name);
        $line =~ /^(\S+)\s*(.+)?$/;
        $account_name = $1;
        $real_name = $2;
        next if not $account_name;
        next if exists $box_names{$account_name};
        push @account_names, $account_name;
        $box_names{$account_name} = $real_name;
    }
    
    if ( not scalar @account_names ) {
        show_lookup(error_message => "No names to lookup.", email_domain => $email_domain);
        return;
    }
    
    if ( not $email_domain ) {
        show_lookup(error_message => "Missing domain name.", box_names => $box_names);
        return;
    }
    
    # call the server to check the email addres availability
    my $tpp_request =  {
	action => 'check',
	object => 'product',
	requestor => {
	    username => $OPENSRS{username},
	},
	attributes => {
	    service => 'email',
	    object_type => 'email',
	    product_data => {
		account_names => [ @account_names ],
		domain => $email_domain,
	    },
	},
    };
    my $lookup_results = $TPP_Client->send_cmd( $tpp_request );
    if ( ! $lookup_results->{is_success} ) {
        error_out("Failed to lookup email availability: ".$lookup_results->{response_text});
        return;
    }

    my @results_array = @{ $lookup_results->{attributes}->{product_data}->{results} };

    my $counter = 0;
    foreach my $result ( @results_array ) {

        $result->{email_address} = $result->{account_name}.'@'.$email_domain;
        $result->{real_name} = $box_names{$result->{account_name}};
        $result->{colouring} = ++$counter % 2 ? "#ffffff" : "#f0f0f0";
        $result->{class} = $counter % 2 ? 'class="accent"' : '';

        $HTML{some_available} = 1 if $result->{available};
    }

    $HTML{results} = \@results_array;
    $HTML{email_domain} = $email_domain;
    
    print_form(template => "$path_templates/lookup_results.html", data => \%HTML);
}

sub verify_user {
    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );
    my $create_new_user = $in{create_new_user};
    my $email_domain = $in{email_domain};
    
    if (not $in{username}) {
        error_out("Empty username.");
        return;    
    }
    
    if (not $in{password}) {
        error_out("Empty password.");
        return;    
    }
    
    
    if($create_new_user) {
	#create the new user
	my $TPP_create_user = {
	    action => 'create',
	    object => 'user',
	    requestor => {
		username => $OPENSRS{username},
	    },
	    attributes => {
		group => "registrants", #is this really necessary?
		username => $in{username},
		password => $in{password},
	    },
	};
	my $create_user_results = $TPP_Client->send_cmd( $TPP_create_user );
	if ( ! $create_user_results->{is_success} ) {
	    error_out("Failed to create user: ".$create_user_results->{response_text});
	    return;
	}
    }
 
    #try to query the user  

    my $TPP_query_user = {
            action => 'query',
            object => 'user',
            requestor => {
                username => $OPENSRS{username},
            },
            attributes => {
                username => $in{username},
            },
    };
    my $query_user_results = $TPP_Client->send_cmd( $TPP_query_user );
    if ( ! $query_user_results->{is_success}) {
	error_out("Failed to query user: ".$query_user_results->{response_text});
	return;
    }
    my $user_id_from_query_user = $query_user_results->{attributes}->{id};

    #now query the domain and compare the user ids
	
    my $TPP_Query_domain =  {
	action => 'query',
	object => 'product',	
	requestor => {
	    username => $OPENSRS{username},
	},
	attributes => {
	    service => 'email',
	    object_type => 'domain',
	    product_data => {
		domain => $email_domain,
	    },
	},
    };
    my $query_domain_results = $TPP_Client->send_cmd( $TPP_Query_domain );
    if ( ! $query_domain_results->{is_success}) {
	unless( $query_domain_results->{attributes} and $query_domain_results->{attributes}->{response_code} == 10511 ){
	    error_out("Failed to query user: ".$query_domain_results->{response_text});
	    return;
	}
    } else {	
	my $user_id_from_query_domain = $query_domain_results->{attributes}->{product_data}->{user_id};
	if ($user_id_from_query_domain != $user_id_from_query_user) {
	    #this guy cannot register anything on this domain
	    error_out("User " . $in{username} . " is not authorized to register emails on $email_domain.");
            return;
	}
    }

    #try to login with this user. 
   
    my $result = $TPP_Client->login_user($in{username},$in{password},$OPENSRS{username}); 
    if( ! $result->{is_success}) {
	#failure...
	error_out("Failed to login user: ".$result->{response_text});
	return;
    } 

    delete $in{error_message};
    %HTML = ( %HTML, %in, message => "User logged in." );
    if ( not $session->{session_order_data} ) {
        $session->add(session_order_data => \%in);
    } else {
        my $session_order_data = get_session_data('session_order_data');
        %HTML = ( %HTML, %{$session_order_data} );
        $session_order_data->{username} = $in{username};
        $session_order_data->{password} = $in{password};
        $session->{session_order_data} = $session_order_data;
    }

    enter_order_data(%HTML);
}

sub enter_order_data {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );
    my $email_domain = $HTML{email_domain};
    my $box_names = $HTML{box_names};
    my $readable_box_names;

    if ( not $box_names ) {
        foreach my $email_address ( keys %HTML ) {
            next if $email_address !~ /(.+)\@(.+)/;
            my $account_name = $1;
            $email_domain = $2;
            next if $email_address =~ /^reg_proceed_(.+)/;
            $box_names .= $account_name.' '.$HTML{$email_address}."\n" if $HTML{'reg_proceed_'.$email_address};
	    if ($HTML{$email_address}) {
            	$readable_box_names .= $account_name.' ('.$HTML{$email_address}.")<br>" if $HTML{'reg_proceed_'.$email_address};
	    } else {
		$readable_box_names .= $account_name."<br>" if $HTML{'reg_proceed_'.$email_address};
	    }
        }

        if ( not $box_names ) {
            show_lookup(error_message => "No accounts selected");
            return;
        }
    } else {
        $readable_box_names = $box_names;
        $readable_box_names =~ s/(\S+)\s*(.+)?(\n|$)/$1 ($2)<br>\n/g;
    }

    $HTML{baseboxamount} = sprintf("%.2f", $REG_EMAIL{base_box_rate});
    $HTML{capacityamount}= sprintf("%.2f", $REG_EMAIL{storage_rate});
    $HTML{imapamount} = sprintf("%.2f", $REG_EMAIL{imap_rate});
    $HTML{email_domain} = $email_domain;
    $HTML{box_names} = $box_names;
    # preserve this data for future generations...
    my $session_order_data = get_session_data('session_order_data');
    $session_order_data->{box_names} = $box_names;
    $session->{session_order_data} = $session_order_data;
    
    $HTML{readable_box_names} = $readable_box_names;
    
    $HTML{initial_capacity} = $REG_EMAIL{base_capacity};
    $HTML{max_capacity_upgrade} = $REG_EMAIL{max_capacity_increments} * $REG_EMAIL{capacity_upgrade_multiples};
    $HTML{capacity_upgrade_list} = build_select_menu($REG_EMAIL{storage_upgrade_list},0);
    
    print_form(template => "$path_templates/enter_order_data.html", data => \%HTML);

}

sub verify_order_data {

    my $verify_error = "";

    if ( $in{box_password} ne $in{box_password_confirm} ) {
        delete $in{box_password_confirm};
        $verify_error .= "Password not confirmed<br>\n";
    }
    if( length($in{box_password}) < 4 or length($in{box_password}) > 20) {
        delete $in{box_password_confirm};
        delete $in{box_password};
	$verify_error .= "Password must be between 4 and 20 characters long<br>\n";
    }
    if ( $in{capacity_upgrade_units} > $REG_EMAIL{max_capacity_increments} ) {
        $verify_error .= "E-mail order exceeds maximum capacity<br>\n";
    }
   
    $in{capacity_upgrade_amount} = $REG_EMAIL{capacity_upgrade_multiples}; 
    $in{total_capacity} = ( $in{capacity_upgrade_units} * $REG_EMAIL{capacity_upgrade_multiples} ) + $REG_EMAIL{base_capacity};
    
    my $box_names = $in{box_names};
    $box_names =~ s/\r//g;
    $box_names =~ s/<br>//g;
    my @box_names = split /\n/, $box_names;
    foreach my $line ( @box_names ) {
        my ($account_name, $real_name);
        $line =~ /^(\S+)\s*(.+)?$/;
        if ( not $1 ) {
            $verify_error .= "List of email accounts is corrupted, please try again.";
            last;
        }
    }
    
    if ( $verify_error ) {
        enter_order_data(error_message => $verify_error, %in);
        return;
    }

    # now add more order data to session ...
    my $session_order_data = get_session_data('session_order_data');

    %in = ( %in, %{$session_order_data} );
    $session->{session_order_data} = \%in;

    enter_contact_data(%in);
}

sub enter_contact_data {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );
    
    my @emails = ();
    
    if ( not $session->{session_order_data} ) {
        show_lookup(error_message => "Missing order data.");
        return;
    }
    my $session_order_data = get_session_data('session_order_data');
    %HTML = (%HTML, %{$session_order_data});
    
    my $box_names = $in{box_names} ? $in{box_names} : $session_order_data->{box_names};
    $box_names =~ s/\r//g;
    $box_names =~ s/<br>//g;
    my @box_names = split /\n/, $box_names;

    my $counter = 0;
    foreach my $line ( @box_names ) {

        $line =~ /^(\S+)\s*(.+)?$/;

        my $account = {
                    account_name => $1,
                    real_name => $2,
                    colouring => ++$counter % 2 ? "#ffffff" : "#f0f0f0",
                    class => $counter % 2 ? 'class="accent"' : '',
                    };
        push @emails, $account;
        
    }

    $HTML{country_menu} = build_country_list($HTML{country});

    $HTML{emails} = \@emails;

    my $TPP_Query_domain =  {
	action => 'query',
	object => 'product',	
	requestor => {
	    username => $OPENSRS{username},
	},
	attributes => {
	    service => 'email',
	    object_type => 'domain',
	    product_data => {
		domain => $HTML{email_domain},
	    },
	},
    };
    my $query_domain_results = $TPP_Client->send_cmd( $TPP_Query_domain );
    if ( ! $query_domain_results->{is_success} ) {
       $HTML{first_email} = 1;
    } else {
       $HTML{first_email} = 0;
    }
    
    print_form(template => "$path_templates/enter_contact_data.html", data => \%HTML);

}

sub retrieve_contact_info {
    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );
 
    my $session_order_data = get_session_data('session_order_data');

    if (not $in{reg_email}) {
        error_out("Empty Account Name.");
        return;    
    }

    my $acc_nm  = $in{reg_email};
    my $dm_nm = $session_order_data->{email_domain};

    my $tpp_request = {
        action => 'query',
        object => 'product',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
            service => 'email',
            object_type => 'email',
            product_data => {
                account_name => $acc_nm,
                domain => $dm_nm,
       	    },
        },
    };

    my $product_info = $TPP_Client->send_cmd( $tpp_request );
    if ((not $product_info->{is_success}) || (not $product_info->{attributes}->{contact_set})) {
        error_out("Could not query product info: ".$product_info->{response_text});
        return;
    }
	
    $tpp_request = {
        action => 'query',
        object => 'contact',
        requestor => {
  	        username => $OPENSRS{username},
        },
        attributes => {
            id => $product_info->{attributes}->{contact_set}->{owner},
        },
    };
	
    my $contact_info = $TPP_Client->send_cmd( $tpp_request );
    if (not $contact_info->{is_success}) {
        error_out("Could not fetch contact info: ".$contact_info->{response_text});
        return;
    }

    %in = ( %in, %{$contact_info->{attributes}}, );
    $in{owner_email} = $contact_info->{attributes}->{email};

    my $new_real_name = $contact_info->{attributes}->{first_name}." ".
                     $contact_info->{attributes}->{last_name};

    my $box_names = $session_order_data->{box_names};
    $box_names =~ s/\r//g;
    $box_names =~ s/<br>//g;
    my @box_names = split /\n/, $box_names;
    my @new_box_names = ();

    my $counter = 0;
    foreach my $line ( @box_names ) {

	$line =~ /^(\S+)\s*(.+)?$/;
	my $new_line = "";

	if ( not $2 ) {
	    $new_line = $1.' '.$new_real_name;
	} else {
	    $new_line = $line;
	}

	push @new_box_names, $new_line;

    }

    $in{box_names} = join "\n", @new_box_names if scalar @new_box_names;

    enter_contact_data(%in);

}

sub verify_contact_data {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );

    my $session_order_data = get_session_data('session_order_data');

    my $contact_data = {};
    
    foreach ( qw(first_name last_name org_name address1 address2 address3 city state country postal_code phone fax owner_email catch_all_email misaddressed_email) ) {
        next if not $in{$_};
        my $full_key = $_;
        $full_key = 'owner_'.$full_key if $_ !~ /^owner_/;
        $contact_data->{$full_key} = $in{$_};
        $session_order_data->{$_} = $in{$_};
    }
    
    foreach ( grep /^domain_admin_/, keys %in ) {
        $session_order_data->{$_} = $in{$_};
    }
    
    foreach ( grep /^real_name_/, keys %in ) {
        $session_order_data->{$_} = $in{$_};
    }

    $session->{session_order_data} = $session_order_data;

    my %result = $TPP_Client->validate_contacts( $contact_data, custom_verify => 'email' );
    if ( ! $result{is_success} ) {
        enter_contact_data(error_message => $result{error_msg}, %in);
    } else {   
        # check catch_all_email here...
        if($in{misaddressed_email} eq 'catch_all' and !OpenSRS::XML_Client::check_email_syntax($in{catch_all_email})) {
           enter_contact_data(error_message => '<b>catch all</b> email is invalid', %in);
        } else {
	   order_confirmation(%in);
        }
    }
}

sub order_confirmation {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );

    my $session_order_data = get_session_data('session_order_data');

    %HTML = ( %HTML,
              %{$session_order_data}, );

    my @emails = ();
    my $box_names = $session_order_data->{box_names};
    $box_names =~ s/\r//g;
    $box_names =~ s/<br>//g;
    my @box_names = split /\n/, $box_names;

    my $counter = 0;
    foreach my $line ( @box_names ) {

        $line =~ /^(\S+)\s*(.+)?$/;

        my $account = {
                    account_name => $1,
                    real_name => $2 || $session_order_data->{'real_name_'.$1},
                    domain_admin => $session_order_data->{'domain_admin_'.$1},
                    colouring => ++$counter % 2 ? "#ffffff" : "#f0f0f0",
                    class => $counter % 2 ? 'class="accent"' : '',
                    };
        push @emails, $account;
        
    }

    my $storage_units = $session_order_data->{capacity_upgrade_units};
    my $this_box_rate = $REG_EMAIL{base_box_rate};
    $this_box_rate += $REG_EMAIL{imap_rate} if $session_order_data->{imap};
    $this_box_rate += $REG_EMAIL{storage_rate} * $storage_units;

    my $final_amount = $this_box_rate * $counter;

    $HTML{AMOUNT} = sprintf("%.2f", $final_amount); 
    $HTML{emails} = \@emails;
      
    $HTML{collect_payment} = $F_SHOW_CC_FIELDS;
    
    my $expmonth = (exists $in{p_cc_exp_mon}) ? $in{p_cc_exp_mon} : 1; 
    $HTML{cc_types} = build_select_menu3(\%cc_types, \@cc_types, $in{p_cc_type});
    $HTML{cc_mons} = build_select_menu(\%cc_mons, $expmonth);
    my $expyear = (exists $in{p_cc_exp_yr}) ? $in{p_cc_exp_yr} : (localtime)[5] + 1900;
    $HTML{cc_years} = build_select_menu(get_cc_years(),$expyear);
    $HTML{cvv_enabled} = $REG_EMAIL{F_ENABLE_CVV};
    
    print_form(template => "$path_templates/order_confirmation.html", data => \%HTML);

}


sub register {

    my %HTML = ( affiliate_id => $in{affiliate_id}, @_ );

    my $session_order_data = get_session_data('session_order_data');

    my $box_names = $session_order_data->{box_names};
    $box_names =~ s/\r//g;
    $box_names =~ s/<br>//g;
    my @box_names = split /\n/, $box_names;

    my $tpp_request = {
	action => 'create',
	object => 'order',
	requestor => {
	    username => $OPENSRS{username},    
	},
	attributes => {
	    handling => ( $REG_EMAIL{process_immediate} ? 'process' : 'save' ),
	    client_reference => 'client-'.time(),
	    username => $session_order_data->{username},
	    password => $session_order_data->{password},
	    contacts => [
		{
		    client_reference => 'client-'.time(),
		    first_name => $session_order_data->{first_name},
		    last_name => $session_order_data->{last_name},
		    org_name => $session_order_data->{org_name},
		    address1 => $session_order_data->{address1},
		    address2 => $session_order_data->{address2},
		    address3 => $session_order_data->{address3},
		    city => $session_order_data->{city},
		    state => $session_order_data->{state},
		    country => $session_order_data->{country},
		    postal_code => $session_order_data->{postal_code},
		    phone => $session_order_data->{phone},
		    fax => $session_order_data->{fax},
		    email => $session_order_data->{owner_email},
		},
	    ],
	},
    };

    my @feature_set = ();
    push @feature_set, 'IMAP' if $session_order_data->{imap};

    my $email_count = 0;
    foreach my $line ( @box_names ) {

        $line =~ /^(\S+)\s*(.+)?$/;

	my $item = {
	    service => 'email',
	    object_type => 'email',
	    client_reference => 'client-'.time(),
	    orderitem_type => 'new',
	    product_data => {
		account_name => $1,
		domain => $session_order_data->{email_domain},
		catch_all_email => $session_order_data->{catch_all_email},
		misaddressed_email => $session_order_data->{misaddressed_email },
		password => $session_order_data->{box_password},
		real_name => $2 || $session_order_data->{'real_name_'.$1},
		f_domain_admin => $session_order_data->{'domain_admin_'.$1},
		capacity_upgrade_units => $session_order_data->{capacity_upgrade_units},
		feature_set => [
		    @feature_set
		],
	    },
	    contact_set => {
		owner => 0,
	    },
	};

	push(@{ $tpp_request->{attributes}->{create_items}},$item);

        $email_count++;
    }

    # only run this test if you set F_VERIFY_CC in conf file
    if ($REG_EMAIL{F_VERIFY_CC}) {

        my $cc_num = $in{p_cc_num};
        my $cc_type = $in{p_cc_type};
        my $cc_exp_mon = $in{p_cc_exp_mon};
        my $cc_exp_yr = $in{p_cc_exp_yr};

	# check the cc number
	if (not cc_verify($cc_num)) {
	    order_confirmation(%in, error_message => "Invalid credit card number.");
	    return;
	}

	# check the expiration date
	if (not cc_exp_verify($cc_exp_mon,$cc_exp_yr)) {
	    order_confirmation(%in, error_message => "Invalid credit card expiration: $cc_exp_mon/$cc_exp_yr.");
	    return;
	}

	if ($REG_EMAIL{F_ENABLE_CVV}) {
	    # check the CVV number
	    if (not defined $in{p_cc_cvv}) {
		order_confirmation(%in, error_message => "Missing CVV number.");
		return;

	    } elsif ($in{p_cc_cvv} !~ /^\d+$/ or
		     length($in{p_cc_cvv}) < 3 or length($in{p_cc_cvv}) > 4) {
		order_confirmation(%in, error_message => "Invalid CVV number.");
		return;
	    }
	}

        my $storage_units = $session_order_data->{capacity_upgrade_units};
        my $this_box_rate = $REG_EMAIL{base_box_rate};
        $this_box_rate += $REG_EMAIL{imap_rate} if $session_order_data->{imap};
        $this_box_rate += $REG_EMAIL{storage_rate} * $storage_units;

        my $final_amount = $this_box_rate * $email_count;
        # So now, with the "final_amount", you can now send a payment
        # request to the payment gateway of your choice.

    }

    my $register_results = $TPP_Client->send_cmd( $tpp_request );
	
    if (not $register_results->{is_success} and $register_results->{response_text} ne 'Insufficient balance') {
        order_confirmation( %in,
                            error_message => 'Failure in order submission: '.$register_results->{response_text});
	return;
    }

    my $counter = 0;
    foreach my $result ( @{$register_results->{attributes}->{create_items}} ) {

        $result->{colouring} = ++$counter % 2 ? "#ffffff" : "#f0f0f0";
        $result->{class} = $counter % 2 ? 'class="accent"' : '';

    }
	
    foreach my $ret_item (@{ $register_results->{attributes}->{create_items}}) {
	$ret_item->{email_address} = $ret_item->{product_item}->{product_data}->{account_name} . '@' . $ret_item->{product_item}->{product_data}->{domain};	
	if($ret_item->{major_code} == 200) {
	    #we hide the money problems from the end user
	    if ($register_results->{response_text} ne 'Insufficient balance') {
		$ret_item->{response_text} = 'E-mail registration successfully completed.';
	    } else {
		$ret_item->{response_text} = 'E-mail registration successfully submitted.';
	    }
	}
    }

    $HTML{register_results} = $register_results->{attributes}->{create_items};
    $HTML{email_domain} = $session_order_data->{email_domain};
    $HTML{order_id} = $register_results->{attributes}->{order_id};
    
    if ( $REG_EMAIL{F_SEND_ORDERS} ) {

        my @ids = ();
        my @account_names = ();
        
        foreach ( @{$register_results->{attributes}->{create_items}} ) {
            next if ($_->{major_code} ne 200);
            
            push @ids, $_->{item_id};
            push @account_names, $_->{product_item}->{product_data}->{account_name};
        }

	if ( not send_email( "$path_templates/order_notification.txt",
		             {
		               %{$session_order_data},
		               mailfrom => $session_order_data->{owner_email}||$ADMIN_EMAIL,
		               mailto => $ADMIN_EMAIL,
		               ids => join(", ", @ids),
                               account_names => join(", ", @account_names),
                               feature_set_text => join(", ", @feature_set),
                               capacity_upgrade_text => $session_order_data->{capacity_upgrade_units}.' x '.$REG_EMAIL{capacity_upgrade_multiples}.'MB',
			       order_id => $register_results->{attributes}->{order_id},
			       p_cc_type => $in{p_cc_type},
			       p_cc_num => $in{p_cc_num},
			       p_cc_exp_mon => $in{p_cc_exp_mon},
			       p_cc_exp_yr => $in{p_cc_exp_yr},
		              } ) ) {
            $HTML{error_message} = "Failed to send notification to ADMIN_EMAIL";
        }
    }
    
    if ( $REG_EMAIL{F_SEND_THANKYOU} &&
         $session_order_data->{owner_email} ) {

        my @accounts_and_ids = ();
        
        foreach ( @{$register_results->{attributes}->{create_items}} ) {
            next if ($_->{major_code} ne 200);
            
            # Text for ASCII email
            #push @accounts_and_ids, $_->{product_item}->{product_data}->{account_name}.'@'.$session_order_data->{email_domain}.
            #                        "\t".$_->{item_id};
            # Text for HTML email
            push @accounts_and_ids, "<tr><td>".$_->{product_item}->{product_data}->{account_name}.'@'.$session_order_data->{email_domain}.
                                    "</td><td>".$_->{item_id}."</td></tr>";
        }

	if ( not send_email( 
                             #"$path_templates/thankyou.txt",
                             "$path_templates/thankyou.html.txt",
		             {
		               %{$session_order_data},
		               mailfrom => $session_order_data->{owner_email}||$ADMIN_EMAIL,
		               mailto => $session_order_data->{owner_email},
		               accounts_and_ids => join("\n", @accounts_and_ids),
			       order_id => $register_results->{attributes}->{order_id},
		             } ) ) {
            $HTML{error_message} = "Failed to send thank you to customer.";
        }
    }
    
    print_form(template => "$path_templates/register_results.html", data => \%HTML);
    
}

sub get_session_data {
    
   my $key = shift;
   return $session->{$key};
}

