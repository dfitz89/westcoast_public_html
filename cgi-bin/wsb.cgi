#!/usr/local/bin/perl
#       .Copyright (C)  2004 TUCOWS.com Inc.
#       .Created:       2004/07/17
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://email.tucows.com
#       .Authors:       Yuliya Gumerova
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
# 
#
use vars qw(%in $cgi $session $path_templates %actions $action $wsb $path_to_config);
# Null these things out for mod_perl users
(%in, $cgi, $session, $path_templates, %actions, $action, $path_to_config) = ();

use constant NUM_SERVERS => 4; # max number of servers a user can specify.

# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
   # first "do" the major config file
   $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
   do "$path_to_config/OpenSRS.conf";
   # now load up the config for EmailDefense services
   do "$path_to_config/WSB.conf";
}

use strict;
use lib $PATH_LIB;
use CGI ':cgi-lib';
use HTML::Template;
use Data::Dumper;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use OpenSRS::Util::ConfigJar "$path_to_config/WSB.conf";
use OpenSRS::Util::Common qw(build_select_menu build_select_menu3 build_country_list build_year_menu build_month_menu build_day_menu);
use OpenSRS::XML_Client;
use OpenSRS::WSB;
use OpenSRS::Util::Session;
use OpenSRS::Language;
use Date::Calc qw(Today);
use POSIX;

# global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/wsb";
%in = ();

%actions = (
		do_start_up  => undef,
	    	display_login => undef,
		recover_password => undef,
		create_new_account => undef,
		transition_actions => undef, 
		do_login => undef, 
		do_update_settings  => undef,
		manage_account => undef,  
	    );

print "Content-type:  text/html\n\n";

# start things up

# set debugging level
set_debugging_level();
init_wsb();

# read in the form data
ReadParse(\%in);
local $Data::Dumper::Purity = 1;
local $Data::Dumper::Deepcopy = 1;
local $Data::Dumper::Ident = 1;

$session = OpenSRS::Util::Session->restore(
               $in{session},
               $in{sign},
               $OPENSRS{private_key});
	   

$action = $in{action};
delete $in{session};
delete $in{sign};
delete $in{action};

process_action($action);

$wsb->logout();

exit;

sub init_wsb {
    $wsb = new OpenSRS::WSB();
    $wsb->init();
}

sub process_action {

    my $action = shift;
   
    #-----------------------------------------------------
    # perform necessary actions

    # no action was supplied, so use the default
    if (not $action) {
        do_start_up();

    # they passed a valid action
    } elsif (exists $actions{$action}) {
	no strict "refs";
	&$action();
	use strict;

    # they passed an invalid action
    } else {
	error_out("Invalid action: $action");
    }
}


# Session functions
####################################################################

# delete default value from session.
sub init_session {
    map { delete $session->{$_} } keys %{$session};
    
}

# load default value from config file into session.
sub load_defaults {

    foreach my $key ( keys %DEFAULT_VALUES ) { 
        $session->{$key} = $DEFAULT_VALUES{$key};
    }
}

# look up a value from session.
sub lookup_value {

    my $key = shift;
    return $session->{$key};
}

# store a value into session.
sub store_value {
   
   my ($key, $value) = @_;   
   $session->{$key} = $value;
}

# just a shorter version of looking up a value of
# "sd_curr_domain_info" from session.
sub lookup_curr_account_value {

    my $key = shift;
    my $curr_account_info = lookup_value('sd_curr_account_info');

    my $value = $curr_account_info->{$key};
    return $value;
}

sub store_curr_account_value {

    my ($key, $value) = @_;

    my $curr_account_info = lookup_value('sd_curr_account_info');
    $curr_account_info->{$key} = $value;

    store_value('sd_curr_account_info',$curr_account_info );
    $curr_account_info = lookup_value('sd_curr_account_info');

}

# clears current domain info and initialises domain's accounts info.
# "Current domain" holds info in the session on the domain being managed or purchased.
sub init_curr_account_info {

    my $curr_account_info = {};
    store_value('sd_curr_account_info', $curr_account_info);
}

sub init_action_history {

    my @action_history = ();
    store_value('action_history', \@action_history);
}


######################### GENERAL FUNCTIONS ###########################################


sub do_start_up {
    my $message = shift;
    start_up();
    display_login($message);
}

sub start_up {
    # delete deafult values from the session.
    init_session();
    init_curr_account_info();
    init_action_history();
    #load the defaults from config file
    load_defaults();
}

sub transition_actions {

    map { $action = $_ if $_ =~  /^do_\w+$/; } keys %in;
    no strict "refs";
    &$action();
    use strict;
}

sub do_cancel_action {

    my $action_history = lookup_value('action_history');
    $action = pop @{$action_history};

    if ($action eq 'display_package_info') {
      store_curr_account_value('probable_package_name', "");
      store_curr_account_value('trial', "");
    } 
    
    $action = pop @{$action_history};
    no strict "refs";
    &$action();
    use strict;
}

sub do_cancel_manage_action {
    
    # return to the list of accounts 
    if ( lookup_value('dflt_enable_rwi2') ) {
        init_curr_account_info();
	get_wsb_accounts();
    # return to the login page.
    } else {
	do_start_up(); 
    }
}

######################### RECOVER PASSWORD FUNCTIONS ###########################################

sub do_display_recover_password {    
    my %HTML;

    $HTML{message} = shift;
    $HTML{username} = $in{username};
    $HTML{action} = 'do_display_recover_password';

    print_form(template => "$path_templates/recover_password.html", data => \%HTML);
}

sub do_recover_password {
    
    my %HTML;

    my $result;
    
    if ( not $in{username} ) {
        do_display_recover_password("Please enter username.");
	exit;
    }
    
    if ( lookup_value('dflt_enable_rwi2') ) {
        $result = $wsb->recover_rwi2_password($in{username});
    } else {
        $result = $wsb->recover_wsb_password($in{username});
    }
    splice ( @{lookup_value('action_history')}, -2 );
    
    if ( $result->{is_success} ) {
        display_login("An email has been sent with your password.");
    } else {
        do_display_recover_password("User \"$in{username}\" does not exist.");   
    }   
 }

######################### LOGIN FUNCTIONS ###########################################


# Lookup is the default page to show if no action is 
# specified
sub display_login {
 
    my %HTML;
    
    $HTML{message} = shift;
    $HTML{enable_manage} = lookup_value('dflt_enable_manage');
    $HTML{send_password} = lookup_value('dflt_enable_send_password');
    $HTML{enable_rwi2}   = lookup_value('dflt_enable_rwi2');
    $HTML{action} = 'do_start_up';
    
    print_form(template => "$path_templates/login.html", data => \%HTML );    
}

# There are three cases of login.
# 1. As RWI2 user.
# 2. As WSB account, when RWI2 user is in the config.
# 3. As WSB account, when RWI2 user is identical (mapping 1<=>1).
sub do_login {
    
    # Login as RWI2 user.    
    if (lookup_value('dflt_enable_rwi2')) {
        store_value('rwi2_username', $in{username});
        store_value('rwi2_password', $in{password});
	login_rwi2_user();  
	get_wsb_accounts();	  
    # Login as WSB account.
    } else {
        # RWI2 user details in config.
        if (lookup_value('dflt_rwi2_username')) {
	    store_value('rwi2_username', lookup_value('dflt_rwi2_username'));
	    store_value('rwi2_password', lookup_value('dflt_rwi2_password'));
	# RWI2 user details from the web, the same as WSB account.
	} else {
    	    store_value('rwi2_username', $in{username});
    	    store_value('rwi2_password', $in{password});  
	}
        store_curr_account_value('account_username', $in{username});
        store_curr_account_value('account_password', $in{password});
        login_rwi2_user();      
        validate_rwi2_owner(); 
        validate_wsb_account();
	manage_account();	
    }
}

# Login RWI2 user.
sub login_rwi2_user {
    
    my $result = $wsb->login_user( lookup_value('rwi2_username'), 
    				   lookup_value('rwi2_password'));
				   
    if ($result->{is_success}) {
        store_value('rwi2_user_id',$result->{attributes}{user_id});
    } else {
	display_login($result->{response_text});
	exit;
    }
}

# Validate that RWI2 user owns the WSB account.
sub validate_rwi2_owner {

    my $account_name = lookup_curr_account_value('account_username');
    my $result = $wsb->query_inv_item_by_description($account_name);
    
    if ($result->{is_success}) {
        if ($result->{attributes}{result}[0]{user_id} ne lookup_value('rwi2_user_id')) {
	    display_login("WSB account \"$account_name\" not found.");
	    exit;
	} else {
	    store_curr_account_value('inventory_item_id', $result->{attributes}{result}[0]{inventory_item_id});
	}
    } else {
	display_login($result->{error});
	exit;
    }
}

# Validate WSB account.
sub validate_wsb_account {

    my $account_username = lookup_curr_account_value('account_username');
    my $account_password = lookup_curr_account_value('account_password');
    
    my $result = $wsb->validate_wsb_account($account_username, $account_password);
    if (not $result->{is_success}) {
	display_login($result->{response_text});
	exit;
    }
}

# Function for Variant 1 after login
sub get_wsb_accounts {
    get_rwi2_user_wsb_accounts();
    query_accounts_by_id();
    do_display_wsb_accounts();
}

######################### CREATE NEW ACCOUNT FUNCTIONS ########################################

# Called from "List WSB accounts" (variant 1) and "Login" pages (variants 2 and 3).
sub do_create_new_account {

    store_value('curr_path', 'create');
    store_value('curr_action', 'create');
  
    # WSB account with RWI2 in config.
    if ( $VARIANT_2 ) {
        
	# Authentication is needed only for variant 2 since 
	# variant 1 is already authenticated and
	# variant 3 gets authenticated after account info is collected.
	store_value('rwi2_username', lookup_value('dflt_rwi2_username'));
	store_value('rwi2_password', lookup_value('dflt_rwi2_password'));
	login_rwi2_user();
    } 
    display_account_info();
}

sub display_rwi2_user {

    my %HTML;
    
    $HTML{message} = shift;
    $HTML{rwi2_username} = $in{rwi2_username};
    $HTML{rwi2_password} = $in{rwi2_password};
    $HTML{rwi2_confirm_password} = $in{rwi2_confirm_password};
    
    print_form(template => "$path_templates/create_rwi2_user.html", data => \%HTML);
}

sub do_create_new_rwi2_user {

    display_rwi2_user();
}

# Collect entered RWI2 user info from the "Create RWI2 user" page.
sub do_collect_rwi2_user_info {
    
    store_value('rwi2_username', $in{rwi2_username});
    store_value('rwi2_password', $in{rwi2_password});
    
    if ( $in{rwi2_confirm_password} ne $in{rwi2_password} ) {
        display_rwi2_user("Password and confirm password do not match.");
	exit;
    }
	
    if ( my $error = create_rwi2_user() ) {
       display_rwi2_user($error);
       exit;
    }
    
    login_rwi2_user();  
    get_wsb_accounts();	  

}

######################### MANAGE ACCOUNT FUNCTIONS ########################################

# Get all WSB accounts belonging to the RWI2 user.
sub get_rwi2_user_wsb_accounts {

    my $page = 0;
    my $page_size = $WSB{NUM_ITEMS_PER_PAGE};
    
    my %data = (    user_id => lookup_value('rwi2_user_id'),
    		    page_size => $page_size,
		    start_index => $page*$page_size + 1,
    );
    
    my $result = $wsb->query_inv_items_created_by_user_id(\%data);
    
    if ($result->{is_success}) {
	my $count = $result->{attributes}{result_control}{record_count};
	my $report_instance_id = $result->{attributes}{result_control}{report_instance_id};        
	my $num_pages = ceil($count/$page_size);
	
	my @wsb_accounts = @{$result->{attributes}{result}};

	for ($page=1; $page<$num_pages; $page++) {
	
	    $data{start_index} = $page*$page_size + 1;
	    $data{report_instance_id} = $report_instance_id;
	
	    $result = $wsb->query_inv_items_created_by_user_id(\%data);
	    
	    if ($result->{is_success}) {
	        @wsb_accounts = (@wsb_accounts, @{$result->{attributes}{result}});
	    } else {
	        error_out($result->{response_text});
	    }
	}
	
	my @sorted_wsb_accounts = sort { $a->{description} cmp $b->{description} } @wsb_accounts;

   	store_value('wsb_accounts', \@sorted_wsb_accounts);
    } else {
        error_out($result->{error});
    }
}

sub query_accounts_by_id {

    my (@wsb_accounts, $wsb_account);
    
    map {
        $wsb_account = query_inv_item_by_id($_->{inventory_item_id});
        push @wsb_accounts, $wsb_account if $wsb_account;
    } @{lookup_value('wsb_accounts')};
    
    store_value('wsb_accounts', \@wsb_accounts);
}

# Function for Variant 2 and 3 after login or Variant 1 after choosing an account from the list.
# Retrieve all info on the account.
sub manage_account {

    my $message =  shift;
    my $inventory_item_id;
   
    # After choosing an account from the list via link all info is lost and has to be restored.
    if ($in{init_session}) {
        start_up();
	$inventory_item_id = $in{inventory_item_id};
	store_value('rwi2_user_id', $in{rwi2_user_id});
    } else {
        $inventory_item_id = lookup_curr_account_value('inventory_item_id');
    }
    
    my $account = query_inv_item_by_id($inventory_item_id);
    error_out("No WSB accounts under the specified brand.") if not $account;
    store_value('sd_curr_account_info', $account);
    store_value('curr_path', 'manage');

    do_display_wsb_account($message);
}

sub query_inv_item_by_id {

    my $inventory_item_id = shift;

    my ($result, @wsb_accounts, $package_title, $package_name, $result_data, $expiry_date, $trial, $wsb_account);
        
    $result = $wsb->query_inv_item_by_id($inventory_item_id);
    
    error_out($result->{response_text}) if not $result->{is_success};

    $result_data   = $result->{attributes}{result}[0];
    $package_name  = $result_data->{product_data}{package_name};
    $package_title = _get_package_title($package_name);
    $trial = $result_data->{product_data}{trial};
    $expiry_date   =  ($result_data->{expiry_date} =~ /^(.*)(\s+00:00:00)$/) ? $1 : ($trial ? "N/A for this status" : "N/A");
    
    $wsb_account = {	
        inventory_item_id => $result_data->{inventory_item_id},
    	account_username  => $result_data->{product_data}{account_username},
    	account_password_mail  => lookup_curr_account_value('account_password'),
    	expiry_date   => $expiry_date,
	last_updated  => $result_data->{last_updated} || "N/A",
    	start_date    => $result_data->{start_date} || "N/A",
    	creation_date => $result_data->{creation_date} || "N/A",
    	contact_id    => $result_data->{contact_set}{owner},
	status        => $result_data->{state},
    	package_name  => $package_name,
    	package_title => $package_title, 
    	language      => $result_data->{product_data}{language},
	trial         => $trial,
    	brand_contact_id => $result_data->{product_data}{brand_contact_id},
    	brand_name       => $result_data->{product_data}{brand_name},
    	brand_url        => $result_data->{product_data}{brand_url},
    	purchase_url     => $result_data->{product_data}{purchase_url},
	ftp_default_directory => $result_data->{product_data}{ftp_default_directory},
	ftp_username	      => $result_data->{product_data}{ftp_username},
	ftp_port	      => $result_data->{product_data}{ftp_port},
	ftp_index_filename    => $result_data->{product_data}{ftp_index_filename},
	ftp_password	      => $result_data->{product_data}{ftp_password},
	ftp_server	      => $result_data->{product_data}{ftp_server},
	domain		      => $result_data->{product_data}{domain},		
	uno => $result_data->{product_data}{brand_supplier_uno_code},
	rwi2_user_id => lookup_value('rwi2_user_id'),
	enable_manage => lookup_value('dflt_enable_manage'),
    } if $result_data->{product_data}{brand_name} eq lookup_value('dflt_brand_name');

    return $wsb_account;
}




######################### ACCOUNT INFO FUNCTIONS ###########################################


sub do_display_wsb_accounts {

    my %HTML;
    
    my $wsb_accounts = lookup_value('wsb_accounts');
    
    if ( not scalar @{$wsb_accounts} ) {
        $HTML{message} = 'No accounts under brand name '.lookup_value('dflt_brand_name');
    } else {
        $HTML{message} = shift;
	$HTML{wsb_accounts} = $wsb_accounts;	
    }
    $HTML{enable_manage} = lookup_value('dflt_enable_manage');  
    $HTML{action} = 'do_display_wsb_accounts';

    print_form(template => "$path_templates/list_wsb_accounts.html", data => \%HTML);
}


sub do_display_wsb_account {

    my %HTML;
    
    %HTML = %{lookup_value('sd_curr_account_info')};

    $HTML{action} = 'do_display_wsb_account'; 
    $HTML{message} = shift; 
    
    $HTML{create_path} = (lookup_value('curr_path') eq 'create'); 
    
    $HTML{allow_upgrade} = lookup_value('dflt_enable_upgrade_package') && 
    			   lookup_curr_account_value('package_name') ne _get_greatest_package_name() && 
			   !lookup_curr_account_value('trial') && 
			   lookup_curr_account_value('status') eq 'active';
			   
    $HTML{allow_set_expiry} =  !lookup_curr_account_value('trial') &&
    				lookup_value('dflt_enable_set_expiry_date') &&
				lookup_curr_account_value('status') eq 'active';
			      
    $HTML{allow_update_settings} = lookup_value('dflt_enable_update_settings');
    
    $HTML{allow_go_live} = lookup_value('dflt_enable_go_live') && 
    			   lookup_curr_account_value('trial') && 
			   lookup_curr_account_value('status') eq 'active';

    print_form(template => "$path_templates/display_wsb_account.html", data => \%HTML);

}


sub do_update_settings {

    my $lost_password_email;
    
    store_value('curr_action', 'update_settings');
    
    my $lost_password_email = _get_lost_password_email(lookup_curr_account_value('account_username'));
    
    my $curr_account = lookup_value('sd_curr_account_info');
    $curr_account->{lost_password_email} = $lost_password_email; 
    $curr_account->{ftp_confirm_password} = $curr_account->{ftp_password};

    %in = %{_get_contact_data_by_id(lookup_curr_account_value('contact_id'))};
           
    %{$curr_account} = (%{$curr_account},%{_get_contact_fields()});
   
    store_value('sd_curr_account_info',$curr_account);

    display_account_info();
}


sub display_account_info {

    my %HTML;
    my $message = shift;
    
    my $user_data = _get_user_fields();
    my $contact_data = _get_contact_fields();

    my $ftp_data = _get_ftp_fields('not_dflt');
    my $ftp_default_data = _get_ftp_fields('dflt');

    my %ftp_updatable_data;
    
    map {
        $ftp_data->{$_} = $ftp_default_data->{$_} if $ftp_default_data->{$_};
    } keys %{$ftp_default_data};
    
    map {
        $ftp_updatable_data{'update_'.$_} = 1 if not $ftp_default_data->{$_};
    } keys %{$ftp_data};
    
    
    my $language = lookup_curr_account_value('language');
    my $languages = lookup_value('dflt_languages');    
    
    %HTML = (%{$user_data}, %{$contact_data}, %{$ftp_data}, %ftp_updatable_data);
    
    $HTML{message} = $message;    
    $HTML{country_menu}  = build_country_list($contact_data->{country});
    $HTML{language_list} = OpenSRS::Language::build_wsb_language_list(Default => $language, Languages => $languages);
    $HTML{display_ftp} = lookup_value('dflt_enable_update_ftp');
    
    $HTML{test_ftp} = lookup_value('dflt_test_ftp');
    $HTML{create_path} = (lookup_value('curr_path') eq 'create');
    $HTML{enable_update_password} = $HTML{create_path} || lookup_value('dflt_enable_update_password');
    
    $HTML{action} = 'display_account_info';
    $HTML{language_name} = $languages->{$language};
    $HTML{language} = $language;

    print_form(template => "$path_templates/edit_account_info.html", data => \%HTML);
}

sub do_collect_account_info {

    if (lookup_value('curr_path') eq 'create') {

        _get_account_info();
    
        if ( my $errors = _validate_account_info() ) {	            
	    display_account_info("Correct and re-enter.<br>$errors");
        } else { 
	    _get_expiry_info ();
            display_package_info();   
	}
    } else {

	my $updatable_data = _get_update_settings();
	
        if ( my $errors = _validate_account_info() ) {	            
	    display_account_info("Correct and re-enter.<br>$errors");
        } else {
	    update_account_settings($updatable_data->{update_settings}) if $updatable_data->{update_settings};
	    update_contacts($updatable_data->{update_contacts}) if $updatable_data->{update_contacts};	
	    update_lost_password_email($updatable_data->{update_lost_password_email}) if $updatable_data->{update_lost_password_email};
            manage_account('Settings updated successfully.');
	}
    }     
}

sub _get_update_settings {

    my (%data);
        
    my $html_user_data = _get_user_fields('html');
    my $html_contact_data = _get_contact_fields('html');
    my $html_ftp_data = _get_ftp_fields('html');
        
    my $curr_user_data = _get_user_fields('curr');
    my $curr_contact_data = _get_contact_fields('curr');
    my $curr_ftp_data = _get_ftp_fields('curr');
    
    my %html_acc_data = (%{$html_user_data}, %{$html_ftp_data});
    my %curr_acc_data = (%{$curr_user_data}, %{$curr_ftp_data});
            
    if ($VARIANT_3 && $html_user_data->{account_password} ne $curr_user_data->{account_password}) {
        update_rwi2_user($html_user_data->{account_password});
    }
    
    if ($html_user_data->{lost_password_email} ne $curr_user_data->{lost_password_email}) {
        $data{update_lost_password_email} = $html_user_data->{lost_password_email}; 
	delete $html_acc_data{lost_password_email};
	delete $curr_acc_data{lost_password_email};   
    }
    
    map {
        if ( $html_contact_data->{$_} ne $curr_contact_data->{$_} ) {
            $data{update_contacts} = $html_contact_data;
	}
    } keys %{$html_contact_data};
        
    map {
        if ( $html_acc_data{$_} ne $curr_acc_data{$_} ) {
	     $data{update_settings} = \%html_acc_data;
	}
    } keys %html_acc_data;
    
    %html_acc_data = (%html_acc_data,%{$html_contact_data});
    
    _store_account_info(\%html_acc_data);
    
    return (\%data);
}

sub update_contacts {

    my $update_contact_data =  shift;
    
    my $attributes = update_contacts_order( $update_contact_data );	    

    my $response = $wsb->update_contacts( $attributes );
    if (not $response->{is_success}) {
	display_account_info("$response->{attributes}{create_items}[0]{major_text}: $response->{response_text} ");
	exit;
    }
}

sub update_account_settings {

    my $error;

    my $update_acc_data =  shift;
    
    my $attributes = update_account_settings_order( $update_acc_data );	    

    my $response = $wsb->update_inventory_item( $attributes );
    
    if (not $response->{is_success}) {
	display_account_info("$response->{attributes}{create_items}[0]{major_text}: $response->{response_text} ");
	exit;
    }
}

sub update_lost_password_email {

    my $lost_password_email = shift;

    my $account_username = lookup_curr_account_value('account_username');
    
    my $response = $wsb->update_lost_password_email($account_username, $lost_password_email);

    if ( not $response->{is_success} ) {
	display_account_info("Error updating lost password email: ".$response->{response_text});
	exit;
    } 
}

sub update_rwi2_user {

    my $new_password = shift;
    
    my @users = ({
    	password => $new_password,
	user_id => lookup_value('rwi2_user_id'),
    });
    
    my $attributes = {
    	users => \@users,
    };
    
    my $response = $wsb->update_rwi2_user($attributes);
    
    if (not $response->{is_success}) {
	display_account_info($response->{response_text});
	exit;
    }
}

######################### PACKAGE INFO FUNCTIONS ###########################################

# No changing expiry date when upgrading.
sub do_upgrade_package {

    my $package_name = lookup_curr_account_value('package_name');
    my $package_title = _get_package_title($package_name);
    
    store_curr_account_value('package_title', $package_title);    
    store_value('curr_action', 'upgrade_package');

    display_package_info();   
}

sub display_package_info {

    my %HTML;
    
    $HTML{message} = shift;
    
    $HTML{packages} =  _make_select_html();
    
    my $enable_set_expiry_date = lookup_value('dflt_enable_set_expiry_date');
    
    if ( $enable_set_expiry_date ) {

        my ($year,$month,$day) = Today();

	my $exp_year = lookup_curr_account_value('exp_year') || $year+1;
	my $exp_month = lookup_curr_account_value('exp_month') || $month;
	my $exp_day = lookup_curr_account_value('exp_day') || $day;
	
	$HTML{years_menu} = build_year_menu($year, $year+10, $exp_year);
	$HTML{months_menu} = build_month_menu($exp_month);
	$HTML{days_menu} = build_day_menu($exp_day);
	$HTML{set_expiry_date} = 1;
    } 
    $HTML{terms_url} = lookup_value('dflt_terms_url');
    $HTML{package_comparison_url} = lookup_value('dflt_package_comparison_url');
    $HTML{trial_enabled} = 'checked' if lookup_curr_account_value('trial');
    $HTML{show_trial} = lookup_value('curr_action') ne 'upgrade_package';
    $HTML{show_expiry} = lookup_value('curr_action') ne 'upgrade_package' && $enable_set_expiry_date;

    $HTML{action} = 'display_package_info';
    
    print_form(template => "$path_templates/select_package.html", data => \%HTML);
}

sub do_collect_package_info {

    my $probable_package_title = _get_package_title($in{package_name});
    store_curr_account_value('probable_package_title', $probable_package_title);    
    store_curr_account_value('probable_package_name', $in{package_name});
    store_curr_account_value('trial', $in{trial});

    _get_expiry_info ();

    if ( my $errors = _validate_package_info() ) {	            
	display_package_info("Correct and re-enter.<br>$errors");
    } else {    
        display_charges_info();   
    } 
}

######################### EXPIRY INFO FUNCTIONS ###########################################



sub do_change_expiry {

    display_change_expiry();
}

sub display_change_expiry {

    my %HTML;
    my $message = shift;
        
    $HTML{message} = $message;
    $HTML{action} = 'display_change_expiry';
    $HTML{account_username} = lookup_curr_account_value('account_username');    
    $HTML{status} = lookup_curr_account_value('trial') ? 'Trial' : 'Live';
    $HTML{package_title} = lookup_curr_account_value('package_title'); 
    $HTML{expiry_date} = lookup_curr_account_value('expiry_date');    
    
    my $expiry_data = _get_expiry_data_from_string();  
    my ($year,$month,$day) = Today();    
    
    $HTML{years_menu} = build_year_menu($year, $year+10, $in{exp_year} || $expiry_data->{exp_year}+1);
    $HTML{months_menu} = build_month_menu($in{exp_month} || $expiry_data->{exp_month});
    $HTML{days_menu} = build_day_menu($in{exp_day} || $expiry_data->{exp_day});

    $HTML{expiry_disabled} = 'disabled' if not lookup_value('dflt_enable_set_expiry_date');

    print_form(template => "$path_templates/change_expiry.html", data => \%HTML);
}


sub do_collect_expiry_info {

    _get_expiry_info(); # get info from browser

    if ( my $errors = _validate_expiry_info() ) {	            
	display_change_expiry($errors);
    } else {  
        change_expiry();
    } 
    exit;
}

sub change_expiry {
        
    my $attributes = update_expiry_order();	    

    my $response = $wsb->update_inventory_item( $attributes );

    if ($response->{is_success}) {
        manage_account("Expiry Date successfully updated.");   
    } else {
        display_change_expiry("$response->{attributes}{create_items}[0]{major_text}: $response->{response_text} ");
    }
}


######################### CHARGES INFO FUNCTIONS ###########################################

sub display_charges_info {

    my %HTML;

    if ( lookup_value('curr_action') eq 'go_live' || !lookup_curr_account_value('trial') ) {
        _get_charges_info();
	$HTML{show_charges} = 1;
    }    

    $HTML{account_username} = lookup_curr_account_value('account_username');
    $HTML{package_name} = lookup_curr_account_value('probable_package_name') || lookup_curr_account_value('package_name');   
    $HTML{package_title} = lookup_curr_account_value('probable_package_title') || lookup_curr_account_value('package_title'); 
    $HTML{status} = (lookup_value('curr_action') eq 'go_live' || !lookup_curr_account_value('trial')) ? 'Live' : 'Trial';
    $HTML{price} = lookup_curr_account_value('price');
    $HTML{cc_fields} = $wsb->cc_fields("$path_templates/cc_fields.html") if $WSB{F_SHOW_CC_FIELDS};
    $HTML{action} = 'display_charges_info';
        
    print_form(template => "$path_templates/show_charges.html", data => \%HTML);

}

sub do_process_payment_info {
    
    process_cc_fields() if $WSB{F_VERIFY_CC};
    
    my $curr_action = lookup_value('curr_action');
    my ($attributes, $message_type);
    
    if ($curr_action eq 'create') {
        if ( $VARIANT_3 ) {
	    my $error = create_rwi2_user();
	    error_out($error) if $error;
	}
        $attributes = create_new_wsb_acccount_order();
    } elsif ($curr_action eq 'upgrade_package') {
        $attributes = upgrade_package_order();    
    } elsif ($curr_action eq 'go_live') {
        $attributes = go_live_order();    
    } else {
        error_out("No valid action.");
    }
    $attributes->{handling} = $WSB{process_immediate} ? 'process' : 'save';
    my $response = $wsb->create_order( $attributes );
 
    if ($response->{is_success}) {
        my $message;
	if ( $WSB{process_immediate} ) {
	    $message = "Order # ".$response->{attributes}{order_id}." processed successfully.";
	    store_curr_account_value('inventory_item_id', $response->{attributes}{create_items}[0]{product_item}{inventory_item_id});
	    manage_account($message);
            send_end_user_message() if lookup_value('dflt_enable_client_messaging');
	} else {
	    $message = "Order # ".$response->{attributes}{order_id}." saved successfully.";
	    if (lookup_value('dflt_enable_rwi2')) {
	        do_display_wsb_accounts($message);
	    } else {
	        do_start_up($message);
	    }
	}
    } else {
        delete_rwi2_user() if $curr_action eq 'create' and $VARIANT_3;
        error_out("$response->{response_text}: $response->{attributes}{create_items}[0]{major_text}");
    }
}

sub send_end_user_message {

    my %DATA;
    
    my $brand_contact_data = _get_contact_data_by_id(lookup_curr_account_value('brand_contact_id'));
    my $user_contact_data = _get_contact_data_by_id(lookup_curr_account_value('contact_id'));
    
    my $message_type = lookup_value('curr_action');
    
    if ($message_type eq 'create') {
    
        # Create Account Trial
        if ( lookup_curr_account_value('trial')) {    
	    $message_type = 'create_trial';
	    
	# Create Account Live       
	} else {
            $DATA{account_name} = lookup_curr_account_value('account_username');
            $DATA{password} = lookup_curr_account_value('account_password_mail');
	    $message_type = 'create_live';
	}
    }
    my $dflt_message_data = lookup_value('dflt_message_data');

    my $curr_message_data = $dflt_message_data->{$message_type};
    
    # Upgrade, Trial Go Live, Create Account Live, Create Account Trial.
    $DATA{mail_from} = $brand_contact_data->{email};
    $DATA{mail_to} = $user_contact_data->{email};
    $DATA{to_first_name} = $user_contact_data->{first_name};
    $DATA{to_last_name} = $user_contact_data->{last_name};
    $DATA{subject} = $curr_message_data->{'subject'};
    $DATA{rsp_wsb_org_name} = $brand_contact_data->{org_name};
    $DATA{rsp_wsb_email} = $brand_contact_data->{email};
    $DATA{phone_number} = $brand_contact_data->{phone};
    $DATA{rsp_brand_domain_name_url} = _make_brand_url_string();
    
    send_email(template => "$path_templates/messaging/$message_type.eml", data => \%DATA);
}

sub _make_brand_url_string {

    my ($brand_url, $uno);

    if ( $brand_url = lookup_curr_account_value('brand_url') ) {
        $brand_url  = "http://".$brand_url if not $brand_url =~ /^http/;	
	$brand_url .= '?u=l'.$uno if $uno = lookup_curr_account_value('uno');
	$brand_url =~ s/\s+//;
    }
    return $brand_url;
}


######################### CREATE RWI2 USER FUNCTIONS ###########################################

sub is_rwi2_avail {
   
    my $attributes = check_rwi2_user_order();

    my $result = $wsb->check_rwi2_user($attributes);
    
    
    if (not $result->{is_success}) {
        error_out($result->{response_text});
    } else {
        return $result->{attributes}[0]{is_available};
    }
}

sub is_wsb_avail {

    my $result = $wsb->query_inv_item_by_description(lookup_curr_account_value('account_username'));
    
    if ($result->{is_success}) {
        # avail if empty result
        if ( scalar @{$result->{attributes}{result}} ) {
	    return 0;
	} else {
	    return 1;
	} 
    } else {
        error_out($result->{error});
    }
}


sub check_rwi2_user_order {

    my @users = ({
        name => lookup_value('rwi2_username'),  
    });

    my $attributes = {
    	users => \@users,
    };

    return $attributes;
}

sub create_rwi2_user {

    my $rwi2_username = lookup_value('rwi2_username');
    my $rwi2_password = lookup_value('rwi2_password');
    my $rwi2_confirm_password = lookup_value('rwi2_password');
    
    my $result = $wsb->create_user($rwi2_username, $rwi2_password, $rwi2_confirm_password);

    return $result->{error} if not $result->{is_success};

    store_value('rwi2_user_id', $result->{attributes}{user_id});
    return;
}

sub delete_rwi2_user {

    my $rwi2_user_id = lookup_value('rwi2_user_id');
    
    my $result = $wsb->delete_rwi2_user($rwi2_user_id);
}


######################### GO LIVE FUNCTIONS ###########################################


sub do_go_live {

    store_value('curr_action', 'go_live');
    display_charges_info();
}

######################### LOGIN WSB ACCOUNT FUNCTIONS ###########################################

sub do_login_wsb_account {

    my %HTML;
     
    $HTML{uno} = lookup_curr_account_value('uno');
    $HTML{txt_user_name} = lookup_curr_account_value('account_username');
    my $result = _get_account_password();
    if ( not $result->{is_success} ) {
       	do_display_wsb_account('Please try to login later.');
	exit; 
    } 

    $HTML{pwd_password} = $result->{attributes}{product_data}{account_password};
    my $reseller_domain_name = lookup_curr_account_value('brand_url');
    $HTML{login_url} = "http://$reseller_domain_name/sebase/common_loginaction.jsp";
    
    print_form(template => "$path_templates/login_wsb_account.html", data => \%HTML, not_framed => 1);
}


######################### ORDER FUNCTIONS ###########################################


sub create_new_wsb_acccount_order {

    my ($attributes, @create_items, @contacts, $product_data ); 

    #my $user_data = lookup_curr_account_value('user_data');
    #my $contact_data = lookup_curr_account_value('contact_data');
    #my $ftp_data = lookup_curr_account_value('ftp_data');
    my $user_data = _get_user_fields();
    my $contact_data = _get_contact_fields();
    my $ftp_data = _get_ftp_fields();
    
    my $language = lookup_curr_account_value('language');
    my $brand_name = lookup_value('dflt_brand_name');
    my $package_name = lookup_curr_account_value('probable_package_name');
    my $trial = lookup_curr_account_value('trial');    
    my $expiry_date = _convert_date_from_digit_to_string() if not $trial and 
    			( lookup_value('dflt_enable_set_expiry_date') or lookup_value('dflt_expiry_period') );
    my $user_id = lookup_value('rwi2_user_id');
    my $domain = lookup_curr_account_value('domain') ;
    
    $product_data = {
    	%{$user_data},
	%{$ftp_data},
        language => $language,
	brand_name => $brand_name,
	package_name => $package_name,
	domain => $domain,
    };
    
    @contacts = ($contact_data);
    
    @create_items = ({
            service => 'wsb',
            object_type => 'account',
            orderitem_type => $trial ? 'trial' : 'new',
            $expiry_date ? (expiry_date => $expiry_date ) : (),
            contact_set => { owner => 0 },
            product_data => $product_data,
        }
    );

    $attributes = {
    	user_id => $user_id,
	create_items => \@create_items,
	contacts => \@contacts,
	handling => lookup_value('dflt_process_immediate') ? 'process' : 'save',   
    };

    return $attributes;
}

sub upgrade_package_order {

    my ($attributes, @create_items, @contacts, $product_data ); 
    my $user_id = lookup_value('rwi2_user_id');
    my $inventory_item_id = lookup_curr_account_value('inventory_item_id');
    my $trial = lookup_curr_account_value('trial');    
    my $expiry_date = _convert_date_from_digit_to_string() if not $trial;
    my $package_name = lookup_curr_account_value('probable_package_name');
        
    $product_data = {
	package_name => $package_name,
	mc_action => 'upgrade',
    };

    @create_items = ({
            service => 'wsb',
            object_type => 'account',
            orderitem_type => 'modcontract',
	    inventory_item_id => $inventory_item_id,
            $expiry_date ? (expiry_date => $expiry_date ) : (),
            product_data => $product_data,
        }
    );

    $attributes = {
    	user_id => $user_id,
	create_items => \@create_items, 
    };
    
    return $attributes;
}

sub update_contacts_order {

    my $contacts = shift;
    my $contact_id = lookup_curr_account_value('contact_id');
    
    my $attributes = {
        id => $contact_id,
        %{$contacts},
    };
        
    return $attributes;
}

sub update_account_settings_order {

    my $inventory_item_id = lookup_curr_account_value('inventory_item_id');
    my $ftp_password = lookup_curr_account_value('ftp_password');
    
    my $product_data = {                       
    	ftp_server => lookup_curr_account_value('ftp_server'),
        ftp_port => lookup_curr_account_value('ftp_port'),
        ftp_username => lookup_curr_account_value('ftp_username'),
        $ftp_password ? (ftp_password =>  $ftp_password ) : (),
        ftp_default_directory => lookup_curr_account_value('ftp_default_directory'),
        ftp_index_filename => lookup_curr_account_value('ftp_index_filename'),
        language => lookup_curr_account_value('language'),
        account_password => lookup_curr_account_value('account_password'),
	domain => lookup_curr_account_value('domain'),
    };

    my $attributes = {
            service => 'wsb',
            object_type => 'account',
            inventory_item_id => $inventory_item_id,
            product_data => $product_data,
    };
    
    return $attributes;
}

sub update_expiry_order {

    my @inventory_items;
    my $expiry_date = _convert_date_from_digit_to_string();
   
    push @inventory_items, {
        inventory_item_id => lookup_curr_account_value('inventory_item_id'),
        service           => 'wsb',
	expiry_date       => $expiry_date,
    };
    
    
    my $attributes = {
        user_id => lookup_value('rwi2_user_id'),
	inventory_items => \@inventory_items,
    };
    
    return $attributes;
}

sub go_live_order {

    my $product_data = {
	mc_action => 'golive',
	package_name => lookup_curr_account_value('package_name'),
    };

    my @create_items = ({
            service => 'wsb',
            object_type => 'account',
            orderitem_type => 'modcontract',
	    inventory_item_id => lookup_curr_account_value('inventory_item_id'),
            product_data => $product_data,
        }
    );

    my $attributes = {
        user_id => lookup_value('rwi2_user_id'),
	create_items => \@create_items,
    };

    return $attributes;


}


######################### VALIDATION FUNCTIONS ###########################################




sub _validate_account_info {

    my ($error, $error_msg);
        
    if ($VARIANT_3 && lookup_value('curr_path') eq 'create') {    
	if ( not is_rwi2_avail() or not is_wsb_avail() ) {
            $error_msg = "Account name is not available.</br></br>";
	}
    }

    my $curr_account = lookup_value('sd_curr_account_info');
    my $validate_passwd = lookup_value('curr_path') eq 'create';
    my $user = lookup_value('dflt_enable_rwi2') ? 'rwi2' : 'wsb';
    
    $error_msg .= $error."</br>" if $error = $wsb->check_username_syntax($user, $curr_account->{account_username});
    if ( $validate_passwd or $curr_account->{account_password} or $curr_account->{confirm_password} ) {
        $error_msg .= $error."</br>" if $error = $wsb->check_password_syntax($user, $curr_account->{account_password},$curr_account->{confirm_password});
    }
    $error_msg .= $error."</br>" if $error = $wsb->check_email_syntax($curr_account->{lost_password_email});
    $error_msg .= $error."</br>" if $error = $wsb->validate_ftp_settings(_get_ftp_fields());
    $error_msg .= $error."</br>" if $error = $wsb->validate_contacts(_get_contact_fields());
    $error_msg .= $error."</br>" if $error = $wsb->check_domain_syntax($curr_account->{domain});
    
    return $error_msg;
}

# Validate that package not available for trial is not select for trial.
sub _validate_package_info {

    my $error;
    
    my $trial = lookup_curr_account_value('trial');
    
    if ( $trial ) {
        my $default_trial;
        my $package_name = lookup_curr_account_value('probable_package_name');

	map {
	   $default_trial = $_->{offertrial} if $package_name eq $_->{key};
	} @{lookup_value('dflt_packages')};

	return "This package is not available for Trial." if $trial ne $default_trial;
    }
    
    return _validate_expiry_info();
}

sub _validate_expiry_info {

    if ( not lookup_curr_account_value('trial') and ( lookup_value('dflt_enable_set_expiry_date') or lookup_value('dflt_expiry_period') ) ) {
    
        my %data;

        $data{exp_year} = lookup_curr_account_value('exp_year');
        $data{exp_month} = lookup_curr_account_value('exp_month');
        $data{exp_day} = lookup_curr_account_value('exp_day');
    
        return $wsb->validate_expiry_info(\%data);
    }
}

######################### AUXILLIARY GET FUNCTIONS ###########################################


sub _get_account_info {

    my %account_info = (%{_get_user_fields('html')},%{_get_contact_fields('html')}, %{_get_ftp_fields('html')});
    _store_account_info(\%account_info);
}

sub _store_account_info {
    
    my $account_info = shift;

    map {
        store_curr_account_value($_, $account_info->{$_});
    } keys %{$account_info};

    store_curr_account_value('language', $in{language}); 

    if ( $VARIANT_3 ) {
        store_value('rwi2_username', lookup_curr_account_value('account_username'));
	store_value('rwi2_password', lookup_curr_account_value('account_password'));
    }        
}

sub _get_upgradable_packages {

    my $package_name = shift;
    my ( $pack, @upgradable_packages, @dflt_packages_bk);
    
    my $dflt_packages = lookup_value('dflt_packages');
    
    while ( @{$dflt_packages} ) {
        $pack = shift @{$dflt_packages};
        push @upgradable_packages, $pack if $pack->{sell}; 
	push @dflt_packages_bk, $pack;
    }
    if ( $package_name ) {
        while ( @upgradable_packages ) {
	    $pack = pop @upgradable_packages;
	    last if $package_name eq $pack->{key};
        }
    }
    store_value('dflt_packages', \@dflt_packages_bk);
    return \@upgradable_packages;    
}


sub _get_package_title {

    my $package_name = shift;
    my $package_title;
        
    map {
        $package_title = $_->{name} if $package_name eq $_->{key};
    } @{lookup_value('dflt_packages')};

    return $package_title;
}


sub _get_greatest_package_name {

    map {    
        return $_->{key} if $_->{sell};
    } @{lookup_value('dflt_packages')};
}


sub _get_expiry_info {

    my ($year,$month,$day) = Today();

    my $exp_year  = $in{exp_year} || $year+1;
    my $exp_month = $in{exp_month} || $month;
    my $exp_day = $in{exp_day} || $day;
    
    store_curr_account_value('exp_year', $exp_year);
    store_curr_account_value('exp_month',$exp_month);
    store_curr_account_value('exp_day',  $exp_day);
}

sub _get_expiry_data_from_string {

    my (%data,$exp_year,$exp_month,$exp_day);
    
    my $expiry_date = lookup_curr_account_value('expiry_date');
    my ($year,$month,$day) = Today();
    
    if ( $expiry_date eq 'N/A') {
    
	$exp_year = $year;
	$exp_month = $month;
	$exp_day = $day;
        
    } else {
	$expiry_date =~ /^(\d+)-(\w+)-(\d+)$/;

	$exp_year = $3;
	$exp_month = $2;
	$exp_day = $1;
	
	$exp_day = $2 if $exp_day =~ /^(0)(\d)$/;

	# Convert month from a string to a digit.
	my @mos = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);

	for (my $i = 1; $i <= 12; $i++) {
     	    $exp_month = $i if $exp_month eq $mos[$i-1];
	}    
    }
	
    $data{exp_year} = $exp_year;
    $data{exp_month} = $exp_month;
    $data{exp_day} = $exp_day;
    
    return \%data;
}

sub _get_charges_info {

    my $price = _get_price();
    store_curr_account_value('price',$price );
}

sub _get_price {

    my ($price, $initial_fee, $total_price);
 
    my $package_name = lookup_curr_account_value('probable_package_name') || lookup_curr_account_value('package_name');
    my $orderitem_type = lookup_value('curr_action') eq 'upgrade_package' ? 'modcontract' : 'new';
    my $inventory_item_id = lookup_curr_account_value('inventory_item_id');
    
    # Obtain from RWI2
    if ( lookup_value('dflt_set_percentage_price') ){
    
        my $result = $wsb->get_product_price($package_name, $orderitem_type, $inventory_item_id);
	
	if ($result->{is_success}) {
	    $initial_fee = $result->{attributes}[0]{ancillary_price};
	    $price = $result->{attributes}[0]{price};
	    $total_price = $initial_fee + $price;
	    $total_price = sprintf '%.2f', $total_price + ($total_price * lookup_value('dflt_price_percentage')/100);
	} else {
	    error_out($result->{response_text});
	}        
	
    # Obtain from config
    } else {        
	map {
	   $price = $_->{price} if $package_name eq $_->{key};
	} @{lookup_value('dflt_packages')};
	$initial_fee = $orderitem_type eq 'new' ? $price : 0;
        $total_price = $initial_fee + $price;
    }
    return $total_price/100;
}

sub _get_contact_data_by_id {

    my $contact_id = shift;
    my $result = $wsb->query_contact_by_id($contact_id);
    
    if ($result->{is_success}) {
        return $result->{attributes}{result}[0];
    } else {
        error_out($result->{response_text});
    }
}


sub _get_user_fields {

    my $source = shift;
    my @user_fields = qw(account_username account_password confirm_password lost_password_email domain);
    my $response = _get_fields(\@user_fields, $source);
    
    return $response;
}



sub _get_contact_fields {

    my $source = shift;

    my @contact_fields = qw(first_name last_name title org_name 
    			    address1 address2 address3 city state 
			    postal_code country phone fax email);
    my $response = _get_fields(\@contact_fields, $source);
        
    return $response;
}


sub _get_ftp_fields {

    my $source = shift;
    
    my @ftp_fields = qw(ftp_server ftp_port ftp_username ftp_password ftp_confirm_password ftp_default_directory ftp_index_filename);
    
    # if dflt_enable_update_ftp = 0, always read only from the config.
    my $type = lookup_value('dflt_enable_update_ftp') ? $source : 'dflt';

    my $response = _get_fields(\@ftp_fields, $type);
    
    $response->{ftp_confirm_password} = lookup_value('dflt_ftp_password') if lookup_value('dflt_ftp_password');
        
    return $response;
}

sub _get_fields {
    
    my $fields = shift;
    my $source = shift;
    
    my ($field_value, %fields_data);
    
     
    foreach ( @{$fields} ) {
        if ($source eq 'dflt') { 
            $field_value = lookup_value('dflt_'.$_);
	} elsif ($source eq 'html') {
	    $field_value = $in{$_};
	} elsif ($source eq 'curr') {
	    $field_value = lookup_value('dflt_'.$_) || lookup_curr_account_value($_);
   	} elsif ($source eq 'not_dflt') {
	    $field_value = $in{$_} || lookup_curr_account_value($_);
	} else {
	    $field_value = lookup_value('dflt_'.$_) || $in{$_} || lookup_curr_account_value($_);
	}
	$field_value =~ s/^\s+|\s+$//g;
	%fields_data = (%fields_data, $_ => $field_value);
    }

    return \%fields_data;
}

sub process_cc_fields {

    my %data = ( 
        p_cc_num => $in{p_cc_num},
	p_cc_type => $in{p_cc_type},
	p_cc_exp_mon => $in{p_cc_exp_mon},
	p_cc_exp_yr => $in{p_cc_exp_yr}    
    );
    my $result = $wsb->verify_cc_fields(\%data);

    error_out($result->{error}) if not $result->{is_success};
}

sub _make_select_html {

    my $curr_package_name = lookup_curr_account_value('package_name');
    my $probable_package_name = lookup_curr_account_value('probable_package_name');

    my ($selected, $html, $trial_avail);
    
    map  {
        $selected = "";
	$trial_avail = "";
	
        $selected = ' selected ' if $probable_package_name and $_->{key} eq $probable_package_name;
	if ( lookup_value('curr_action') ne 'upgrade_package' ) {
	    $trial_avail = $_->{offertrial} ? " (Trial Available)" : " (Trial Not Available)";
	}
		
        $html .= "<option value=".$_->{key}."$selected>".$_->{name}.$trial_avail;
    } @{_get_upgradable_packages($curr_package_name)};

    return $html;
}

sub _convert_date_from_digit_to_string {
    
    my $exp_year = lookup_curr_account_value('exp_year');
    my $exp_month = lookup_curr_account_value('exp_month');
    my $exp_day = lookup_curr_account_value('exp_day');
    
    # Convert month from a digit to a string.
    my @mos = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);

    for (my $i = 1; $i <= 12; $i++) {
         $exp_month = $mos[$i-1] if $exp_month eq $i;
    }   
     
    return "$exp_day-$exp_month-$exp_year";
}

sub _get_account_password {

    my $account_username = lookup_curr_account_value('account_username');
    
    my $result = $wsb->get_account_password($account_username);
    
    return $result;    
}

sub _get_lost_password_email {

    my $account_username = lookup_curr_account_value('account_username');
    
    my $result = $wsb->get_lost_password_email($account_username);
        
    if ( not $result->{is_success} ) {
        my $message = $result->{response_code} eq 50037 ? 'Please update settings later.' : $result->{response_text};
	do_display_wsb_account($message);
	exit;
    } else {
        return $result->{attributes}{product_data}{email};
    }
}


sub do_test_ftp_settings {
    
    my $ftp_data = _get_ftp_fields('html');
    
    if (not $ftp_data->{ftp_password}) {
	$ftp_data->{ftp_password} = lookup_curr_account_value('ftp_password');
	$ftp_data->{ftp_confirm_password} = lookup_curr_account_value('ftp_password');
    }
    my $message = $wsb->test_ftp_settings($ftp_data);
    
    $message = "FTP Settings tested successfully." if $message eq 1;
#    store_value('curr_action', 'test_ftp_settings');
    display_account_info($message);
}



##########################################################################
# substitute values on the specified template and print it to the client

# an optional 'type' arg can be passed: 'framed' specifies to pull in base.html
# as the outer frame and the given template as the inner frame
# 'single' specifies to use the given template alone
# the default behavior is 'framed'
sub print_form {
    my %args = @_;
    
    my @action_history = @{lookup_value('action_history')};
    
    push @action_history, $args{data}{'action'} if $action_history[$#action_history] ne $args{data}{'action'};
    store_value('action_history',\@action_history);
    
    if (1) { #for easy debug test
	local $Data::Dumper::Indent=1;
	local $Data::Dumper::Useqq=0;
	#print "<pre>",Dumper(\%args),"</pre>";
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

sub set_debugging_level {

    if ($WSB{debug}) {
	# print error to the page
	select (STDOUT); $| = 1;
	open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
	select (STDERR); $| = 1;
	select (STDOUT);
    }
    
    OpenSRS::Util::Common::initialize( path_templates => $PATH_TEMPLATES );
}

sub error_out {

    my %HTML = ( ERROR => shift );   
    print_form(template => "$path_templates/error.html", data => \%HTML);
    exit;    
}



sub send_email {

    my %args = @_;

    my ( $mail_type, $mail_prog );

    $mail_type = $MAIL_SETTINGS{MAIL_TYPE};
    $mail_prog = $MAIL_SETTINGS{MAILPROG};

    my $temp = HTML::Template->new(cache => 1, filename => $args{template}, die_on_bad_params => 0);
    $temp->param(CGI=>$cgi,%{$args{data}});
    
    my $message = $temp->output;

    my $mailto = $args{data}{mail_to};
    my $mailfrom = $args{data}{mail_from};

    if ($mail_type eq 'sendmail') {
        open (MAIL, "|$mail_prog") or die "Can't open $mail_prog: $!\n";
        print MAIL $message;
        close MAIL or return undef;
    } else {
        OpenSRS::Util::Common::_send_smtp_mail(
		$mailto, $mailfrom, $message
	) or return undef;
    }
    return 1;
}

1;
