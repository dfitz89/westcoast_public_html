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
use vars qw(%in $cgi $session $path_templates %actions $action $antispam $path_to_config);
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
   do "$path_to_config/EmailDefense.conf";
}

use strict;
use lib $PATH_LIB;
use CGI ':cgi-lib';
use HTML::Template;
use Data::Dumper;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use OpenSRS::Util::ConfigJar "$path_to_config/EmailDefense.conf";
use OpenSRS::Util::Common qw(send_email build_select_menu build_select_menu3 build_country_list make_navbar);
use OpenSRS::XML_Client;
use OpenSRS::EmailDefense;
use OpenSRS::Util::Session;


# global defines
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/emaildefense";
%in = ();

%actions = (
	    start_up => undef,

	    lookup_domain => undef,
            recover_password => undef,
	    do_recover_password => undef,
	    login_domain_user => undef,
	    login_user => undef,
	    select_service_action => undef,
	    create_new_user => undef,
	    
	    add_user_accounts => undef,
	    do_add_user_accounts => undef,
	    do_add_user_roles_and_pass_info => undef,
	    process_new_purchase_order => undef,
	    
	    manage_service => undef,
	    do_manage_service => undef,
	    do_manage => undef,
	    do_add_email_servers => undef,
	    add_manage_user_accounts => undef,
	    do_add_contact_info => undef,
	    confirm_add_manage_order => undef,	    
	    
	    remove_manage_user_accounts  => undef,
	    confirm_remove_manage_order => undef,
	    
	    list_features_and_users => undef,

	    cancel_new_purchase_order => undef,
	    cancel_emaildefense_service => undef,
	    do_cancel_emaildefense_service => undef,
	    
	    edit_user_accounts => undef,
	    edit_contact_info => undef,
	    
	    edit_manage_user_accounts => undef,
	    
	    edit_remove_manage_user_accounts => undef,
	    
	    );

print "Content-type:  text/html\n\n";

# start things up

# set debugging level
set_debugging_level();
init_antispam();

# read in the form data
ReadParse(\%in);
local $Data::Dumper::Purity = 1;
local $Data::Dumper::Deepcopy = 1;

$session = OpenSRS::Util::Session->restore(
               $in{session},
               $in{sign},
               $OPENSRS{private_key});
$action = $in{action};
delete $in{session};
delete $in{sign};
delete $in{action};

process_action($action);

$antispam->logout();

exit;

sub init_antispam {
    $antispam = new OpenSRS::EmailDefense();
    $antispam->init();
}

sub process_action {

    my $action = shift;
   
    #-----------------------------------------------------
    # perform necessary actions

    # no action was supplied, so use the default
    if (not $action) {
        start_up();

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
sub delete_defaults {

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
sub lookup_curr_domain_value {

    my $key = shift;
    my $curr_domain_info = lookup_value('sd_curr_domain_info');

    my $value = $curr_domain_info->{$key};
    return $value;
}

sub store_curr_domain_value {

    my ($key, $value) = @_;
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    $curr_domain_info->{$key} = $value;
    store_value('sd_curr_domain_info',$curr_domain_info );
}

# clears current domain info and initialises domain's accounts info.
# "Current domain" holds info in the session on the domain being managed or purchased.
sub init_curr_domain_info {

    my $curr_domain_info = {};
    store_value('sd_curr_domain_info', $curr_domain_info);
    init_domain_accounts_info();
}

# initialises current domain info to the domain's values.
sub get_current_domain_info {

    init_curr_domain_info();
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    $curr_domain_info->{domain_name} = $in{domain_name};
    $curr_domain_info->{inventory_item_id} = $in{inventory_item_id};
    
    store_value('sd_curr_domain_info', $curr_domain_info );
    
    get_domain_accounts_info();    
}

# info about domain's accounts is cleaned.
sub init_domain_accounts_info {

    my @old_user_accounts = ();
    my @old_user_accounts_string = ();
    
    # 'mod_' is used for added or removed.
    my @mod_user_accounts = ();
    my @mod_user_accounts_string = ();
    my @probable_mod_user_accounts_string = ();
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    $curr_domain_info->{old_user_accounts} = \@old_user_accounts;
    $curr_domain_info->{old_user_accounts_string} = \@old_user_accounts_string;
    
    $curr_domain_info->{mod_user_accounts} = \@mod_user_accounts;
    $curr_domain_info->{mod_user_accounts_string} = \@mod_user_accounts_string;
    
    $curr_domain_info->{probable_mod_user_accounts_string} = \@probable_mod_user_accounts_string;

    store_value('sd_curr_domain_info', $curr_domain_info );

}

# Get info of all accounts on the current domain.
# Store the gotten info in the session in "curr_domain_info".
sub get_domain_accounts_info {

    my $result = $antispam->get_domain_accounts_info($in{inventory_item_id});
    
    error_out($result->{response_text}) if not $result->{is_success};
    error_out("This domain has been deleted. You cannot perform any operation on it. Your list of domains will be updated within 8 hours to exclude deleted domain.") 
        if $result->{attributes}{result}[0]{state} eq 'deleted';
            
    my @old_user_accounts = ();
    my @old_user_accounts_string = ();
        
    
    map {    
        push @old_user_accounts, { name => $_->{name}, role => $_->{role}, feature_set => $_->{feature_set}};
    } @{$result->{attributes}{result}[0]{product_data}{accounts}};
    
    map {
        push @old_user_accounts_string, $_->{name};
    } @old_user_accounts;
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    if (scalar @old_user_accounts_string == 1) {
        $curr_domain_info->{disallow_remove_user_account} = 1;
    }    
    
    $curr_domain_info->{old_user_accounts} = \@old_user_accounts;
    $curr_domain_info->{old_user_accounts_string} = \@old_user_accounts_string;
    
    store_value('sd_curr_domain_info', $curr_domain_info );
    
}

# get all domains with antispam for a particular user, by page.
sub get_antispam_domains_by_user {

        my $domain_user_id = lookup_value('sd_domain_user_id') || $in{domain_user_id};
	
	my %data = ( user_id => $domain_user_id );
	
	my $result = $antispam->get_antispam_domains_by_user( \%data );
		
	return $result;
}


######################### GENERAL FUNCTIONS ###########################################


sub start_up {
    # delete deafult values from the session.
    delete_defaults();
    #load the defaults from config file
    load_defaults();
    show_lookup();
}

# Lookup is the default page to show if no action is 
# specified
sub show_lookup {
    
    # start every lookup with a clean info about the domain.
    init_curr_domain_info();

    # if defaults contain domain name, 
    # proceed to the next action without displaying html for domain entry.
    if(lookup_value('dflt_domain_name')){
	store_curr_domain_value ('domain_name',lookup_value('dflt_domain_name'));
	do_lookup_domain();
    } else {
        print_form(template => "$path_templates/lookup.html");
    }
}

sub lookup_domain {
    
    my $domain_name = $in{domain_name};
    error_out("Empty domain") if not $domain_name;
    store_curr_domain_value ('domain_name',$domain_name);
    do_lookup_domain();
}

# Check if domain exists, does not exist, 
# or is already taken and belongs to a different reseller. 
# If the domain is taken and belongs to a different reseller, error out.
sub do_lookup_domain {

    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    my $domain_name = $curr_domain_info->{domain_name};
    my $result = $antispam->check_domain($domain_name);

    if ($result->{is_success}) {
        $curr_domain_info->{available} = $result->{available};
	
	# looping can be removed after API is fixed to return only active domains.
	foreach my $item (@{$result->{attributes}{result}}) {
		$curr_domain_info->{inventory_item_id} = $item->{inventory_item_id};
  	        store_value('sd_domain_user_id',$item->{user_id});
	} 
	store_value ('sd_curr_domain_info',$curr_domain_info);
        select_service_action();
    } else {
        error_out($result->{error});
    }
}


# If domain does not exist, login as existing or new user.
# If domain exists and belongs to the querying reseller, login as existing user.
sub select_service_action {

#    store_username_and_password();

    if (lookup_curr_domain_value('available')) {   
    	new_purchase_service_login();
    } else {
    	manage_service_login();
    }
}

sub store_username_and_password {
    
    my ($username, $password, $error, $result);
    
    if(lookup_value('dflt_username')){
        $username = lookup_value('dflt_username');
        $password = lookup_value('dflt_password');
    } else {
        $username = $in{username};
        $password = $in{password};      
    }
    
    $result = $antispam->check_username_syntax($username); 
    $error .= $result->{error} if not $result->{is_success};
    #$result = $antispam->check_password_syntax($password);
    #$error .= $result->{error} if not $result->{is_success};
    
    error_out($error) if $error;
    
    store_value('sd_username', $username);
    store_value('sd_password', $password);
}

sub create_new_user {

    store_username_and_password();
    store_value('sd_confirm_password',$in{confirm_password}) if not lookup_value('sd_confirm_password'); 

    my $result = $antispam->create_user( lookup_value('sd_username'), 
					 lookup_value('sd_password'),
					 lookup_value('sd_confirm_password'),
					);
    
    error_out($result->{error}) if not $result->{is_success};
    store_value('sd_domain_user_id', $result->{attributes}{user_id});
    new_purchase_service();
}



# Password is emailed to the user.
sub recover_password {

    print_form(template => "$path_templates/recover_password.html");
}


sub do_recover_password {
    
    my %HTML;

    $HTML{domain_name} = lookup_curr_domain_value('domain_name');
    my $result = $antispam->recover_password($in{username});
    
    if ($result->{is_success}) {
        print_form(template => "$path_templates/password_recovery_msg.html", data => \%HTML );
    } else {
        error_out($result->{error});
    }
}

sub new_purchase_service_login {    
    
    store_curr_domain_value('service_type','new_purchase');    
    if(lookup_value('dflt_username')){
        login_user();
    } else {    
        my %HTML;
	$HTML{domain_name} = lookup_curr_domain_value('domain_name');
        print_form(template=> "$path_templates/new_purchase_service_login.html", data => \%HTML);
    }
}

# Login user for the purchase of new domain.
sub login_user {
    
    store_username_and_password();
    my $result = $antispam->login_user( lookup_value('sd_username'), 
    					lookup_value('sd_password'));

    if ($result->{is_success}) {
        store_value('sd_domain_user_id',$result->{attributes}{user_id});
        new_purchase_service();
    } else {
        error_out($result->{error});
    }
}

sub new_purchase_service {

    my %HTML;
     
	add_user_accounts();
}


sub manage_service_login {

    if(lookup_value('dflt_username')){
        login_domain_user();
    } else {
        print_form(template => "$path_templates/manage_service_login.html");
    }
}



# login user only if queried domain belongs to the user for managing.
sub login_domain_user {

    store_username_and_password();  

    my $result = $antispam->login_domain_user(  lookup_value('sd_username'), 
    						lookup_value('sd_password'), 
						lookup_value('sd_domain_user_id')
					     );    
    if ($result->{is_success}) { 
        manage_service();
    } else {
        error_out($result->{error});
    }
}


# store all domains and info on each of them in the session.
sub manage_service {

    my (%HTML, $result, $domain, @sd_domains);
    
    load_defaults();   

    store_value('sd_domain_user_id', $in{domain_user_id}) if $in{domain_user_id};
    
    $domain = $in{domain_name} || lookup_curr_domain_value('domain_name');
    
    if (lookup_value('dflt_manage_one_domain')) {
	$result = $antispam->get_domain_info( $domain );
    } else {
        $result = get_antispam_domains_by_user();
    }
    
    error_out($result->{error}) if not $result->{is_success};
    error_out("There are no Email Defense Service domains to manage as your order has not been processed yet.") 
        if not scalar @{$result->{attributes}{result}};

    foreach $domain ( @{$result->{attributes}{result}} ) {
	push @sd_domains, {
		  domain_name => $domain->{description},
		  inventory_item_id => $domain->{inventory_item_id},
	};
    }
    
    my @sd_domains = sort { $a->{domain_name} cmp $b->{domain_name} } @sd_domains;
    
    store_value('sd_domains', \@sd_domains);
    
    do_manage_service();
}

# display all domains, with each domain keeping a session in case it is going to be managed.
sub do_manage_service {

    my (%HTML, @html_domains, $domain, $i);
    
    init_curr_domain_info();
    store_curr_domain_value('service_type','manage');        

    my %ss = $session->dump($OPENSRS{private_key});
	    
    foreach $domain ( @{lookup_value('sd_domains')} ) {
	push @html_domains, {
		  domain_name => $domain->{domain_name},
		  inventory_item_id => $domain->{inventory_item_id},
		  class => $i%2 ? 'soft' : 'accent',
		  session => $ss{session},
		  sign => $ss{sign},
	};
	$i++;
    }

    $HTML{domains} = \@html_domains;
    $HTML{navbar} = lookup_value('sd_navbar');
    
    print_form(template => "$path_templates/manage_service.html", data => \%HTML);
}

# mix and match different functions for different actions to be performed.
sub do_manage {

    if($in{cancel}) {
        if ($in{edit_path}) {
	     process_action($in{cancel_edit_action});
	} else {
             do_manage_service();    
	}
    } elsif($in{add_manage_user_accounts}) {
        add_manage_user_accounts();
    } elsif($in{add_manage_user_roles_and_pass_info}) {
        do_add_manage_user_accounts();
        add_user_roles_and_pass_info();
    } elsif($in{confirm_add_manage_order}) {
	do_add_manage_user_roles_and_pass_info();
        confirm_add_manage_order();
    } elsif($in{process_add_manage_order}) {
        process_add_manage_order();
    } elsif($in{remove_manage_user_accounts}) {
	remove_manage_user_accounts();
    } elsif($in{confirm_remove_manage_order}) {
	do_remove_manage_user_accounts();
        confirm_remove_manage_order();
    } elsif($in{process_remove_manage_order}) {
        process_remove_manage_order();
    }
}


######################## USER ACCOUNTS #########################################

sub add_user_accounts {

    get_current_domain_info() if $in{init_curr_domain};

    my $HTML = get_basic_user_accounts_html();    
    
    print_form(template => "$path_templates/add_user_accounts.html", data => $HTML );
}

sub add_manage_user_accounts {
    
    get_current_domain_info() if $in{init_curr_domain};

    my $HTML = get_basic_user_accounts_html();
    
    print_form(template => "$path_templates/add_manage_user_accounts.html", data => $HTML );
}

sub remove_manage_user_accounts {
    
    get_current_domain_info() if $in{init_curr_domain};

    my $HTML = get_basic_user_accounts_html();
    
    print_form(template => "$path_templates/remove_manage_user_accounts.html", data => $HTML );
}
    

sub edit_user_accounts {

    my $HTML = get_edit_user_accounts_html();
    
    print_form(template => "$path_templates/add_user_accounts.html", data => $HTML );
}

sub edit_manage_user_accounts {

    my $HTML = get_edit_user_accounts_html();

    print_form(template => "$path_templates/add_manage_user_accounts.html", data => $HTML );
}

sub edit_remove_manage_user_accounts {
    
    my $HTML = get_edit_user_accounts_html();

    print_form(template => "$path_templates/remove_manage_user_accounts.html", data => $HTML );

}

sub get_basic_user_accounts_html {

    my %HTML;

    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    $HTML{domain_name} = $curr_domain_info->{domain_name};
    $HTML{max_users} = $ANTISPAM{MAX_USERS};
    $HTML{disallow_remove_user_account} = $curr_domain_info->{disallow_remove_user_account};
	
    return \%HTML;
}

sub get_edit_user_accounts_html {
    
    my $HTML;
    
    $HTML = get_basic_user_accounts_html();
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    $HTML->{user_accounts} = join "\n", @{$curr_domain_info->{probable_mod_user_accounts_string}};
    
    # if we want to edit previously selected user accounts,
    # we need to clear previous selection.
    $HTML->{edit_path} = 1;	
    
    return $HTML;
}

sub do_add_user_accounts {
    
    confirm_new_purchase_order() if $in{cancel};

    my @mod_user_accounts_string = split " ", $in{mod_user_accounts_string};
    
    my $result = $antispam->check_user_accounts($ANTISPAM{MAX_USERS}, \@mod_user_accounts_string);
    error_out($result->{error}) if not $result->{is_success};
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    $curr_domain_info->{probable_mod_user_accounts_string} = \@mod_user_accounts_string;
    store_value('sd_curr_domain_info', $curr_domain_info );
	
    add_user_roles_and_pass_info();

}

sub do_add_manage_user_accounts {
	    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    my @mod_user_accounts_string = split " ", $in{mod_user_accounts_string};
    
    my $old_user_accounts_string = $curr_domain_info->{old_user_accounts_string};

    my $result = $antispam->check_add_user_accounts($ANTISPAM{MAX_USERS}, \@mod_user_accounts_string, $old_user_accounts_string);
    error_out($result->{error}) if not $result->{is_success};
    
    $curr_domain_info->{probable_mod_user_accounts_string} = \@mod_user_accounts_string;
    store_value('sd_curr_domain_info', $curr_domain_info );
}

sub do_remove_manage_user_accounts {

    if ( ($in{confirm_remove_manage_order} and exists $in{mod_user_accounts_string}) or not $in{confirm_remove_manage_order} ) {

	my $curr_domain_info = lookup_value('sd_curr_domain_info');
        
	my @mod_user_accounts_string = split " ", $in{mod_user_accounts_string};
	
	my $old_user_accounts_string = $curr_domain_info->{old_user_accounts_string};

	my $result = $antispam->check_remove_user_accounts($ANTISPAM{MAX_USERS}, \@mod_user_accounts_string,$old_user_accounts_string);
	error_out($result->{error}) if not $result->{is_success};
	
        $curr_domain_info->{probable_mod_user_accounts_string} = \@mod_user_accounts_string;
        store_value('sd_curr_domain_info', $curr_domain_info );
    }
}

######################################## USER ROLES AND PASSWORD INFO #######################################

sub add_user_roles_and_pass_info {

    my (%HTML, @html_users, $user_accounts);

    if ( not lookup_value('dflt_allow_passwd_assgnmt') and lookup_value('dflt_user_role') ) {
        if ( lookup_curr_domain_value('service_type') eq 'new_purchase' ) {
	    do_add_user_roles_and_pass_info();
	} else {
	    collect_user_info();
	    confirm_add_manage_order();
	}
    } else {
    
    	my @html_users_old_added = ();
    	my @html_users_new_added = ();
    	my $user_accounts_remaining_string = ();
    	my $itr = 0;
    	
    	my $curr_domain_info = lookup_value('sd_curr_domain_info');
    	
    	my $user_accounts_new_added_string = $curr_domain_info->{probable_mod_user_accounts_string};  

    	if ( $HTML{edit_path} = $in{edit_path} ) { 
    	
    	    my $user_accounts_old = $curr_domain_info->{mod_user_accounts};

    	    # if after edit we have the same user accounts, we don't want to include them again.
    	    my $result = $antispam->get_edit_user_accounts($user_accounts_new_added_string, $user_accounts_old);

    	    # prune newly added accounts that are already in the session.
    	    $user_accounts_new_added_string = $result->{user_accounts_new_added_string};
    	    $user_accounts_remaining_string = $result->{user_accounts_remaining_string};

    	    @html_users_old_added = @{get_mod_html_users($user_accounts_remaining_string)};
    	    $itr = scalar @{$user_accounts_remaining_string};
    	} 
    	
    	@html_users_new_added = @{get_default_html_users($user_accounts_new_added_string, $itr)};    

    	@html_users = ( @html_users_old_added, @html_users_new_added);

    	$HTML{users} = \@html_users;
    	$HTML{domain_name} = $curr_domain_info->{domain_name};
    	$HTML{allow_passwd_assgnmt} = lookup_value('dflt_allow_passwd_assgnmt');
    	$HTML{new_purchase} = ( lookup_curr_domain_value('service_type') eq 'new_purchase' ) ? 1 : 0;
	
    	print_form(template => "$path_templates/add_user_roles_and_pass_info.html", data => \%HTML);
    }
}

sub get_default_html_users {

    my $user_accounts_string = shift;
    my $itr = shift;
    
    my @html_users;
         
    map { push @html_users, { user_account => $_,
    			      user_roles => build_select_menu(lookup_value('dflt_user_roles'),lookup_value('dflt_html_user_role') ),
			      itr => $itr++,
		            }
    } @{$user_accounts_string};
    
    return \@html_users;
}

sub get_mod_html_users {
 
    my $user_accounts = shift;
    my @html_users;
    
    my $itr = 0;
    map { push @html_users, { user_account => $_->{user_account},
    			      user_roles  => build_select_menu(lookup_value('dflt_user_roles'), $_->{user_role}),
			      now_enabled => ( $_->{passwd_assgnmt} eq 'now' ) ? "checked" : "",
			      later_enabled => ( $_->{passwd_assgnmt} eq 'later' ) ? "checked" : "",
			      itr => $itr++,
		            }  
    } @{$user_accounts};

   return \@html_users;    
}


sub do_add_user_roles_and_pass_info {
    
    confirm_new_purchase_order() if $in{cancel};
    
    collect_user_info();
    
    if ( $in{edit_path} ) {
	confirm_new_purchase_order();
    } else {
        add_email_servers();    
    }
}

sub do_add_manage_user_roles_and_pass_info {
    
    if ( ($in{confirm_add_manage_order} and exists $in{list}) or not $in{confirm_add_manage_order} ) {
	collect_user_info();
    }
}

sub collect_user_info {

   my (@data, @user_accounts_string, $user_account, $itr, $password, $confirm_password, $passwd_assgnmt, $user_role);

   my $curr_domain_info = lookup_value('sd_curr_domain_info');
   my $dflt_user_role = lookup_value('dflt_user_role');
   
   @user_accounts_string = @{$curr_domain_info->{probable_mod_user_accounts_string}};	 

   $itr=0;
   foreach $user_account ( @user_accounts_string ) {

	$password = $in{'password_'.$itr};
	$confirm_password = $in{'confirm_password_'.$itr};
	$passwd_assgnmt = $dflt_user_role ? 'later' : $in{'passwd_assgnmt_'.$itr};
	$user_role = $dflt_user_role || $in{'user_role_'.$itr};
       
	if ( $passwd_assgnmt eq 'now' ) {
           my $result = $antispam->check_edef_user_password($passwd_assgnmt,$password,$confirm_password) ;
           error_out($result->{error}) if not $result->{is_success};
	}
	
	push @data, { user_account => $user_account,
   		      user_role => $user_role,
   		      passwd_assgnmt => $passwd_assgnmt,
   		      password => $password, 
   		      confirm_password => $confirm_password,
	};
	$itr++;
   }

   $curr_domain_info->{probable_mod_user_accounts} = \@data;
 
   store_value('sd_curr_domain_info', $curr_domain_info );
}

################################ EMAIL SERVERS #########################
sub add_email_servers {

    my (%HTML, $server_info, $i);
    
    if ($server_info = lookup_value('dflt_server_1') ) {
        $i=1;
        while ($server_info = lookup_value('dflt_server_'.$i)){
	    
	    # preference number is optional.
	    $server_info =~ /^(.*),\s*(.*),\s*(.*)$/ or $server_info =~ /^(.*),\s*(.*)$/;

            process_email_servers($i,$1,$2,$3);	   
	    $i++;
        }

        add_contact_info();	

    } else { 
    
        $HTML{domain_name} = lookup_curr_domain_value('domain_name');
        print_form(template => "$path_templates/add_email_servers.html", data => \%HTML );
    }
}


sub do_add_email_servers {
    
    confirm_new_purchase_order() if $in{cancel};
    
    error_out("No email servers specified.") if not $in{'host_1'};
    
    for my $i (1 .. NUM_SERVERS) {
        if ( $in{'host_'.$i} ) {
            process_email_servers($i,$in{'host_'.$i},$in{'port_'.$i},$in{'preference_'.$i});
	}
    }    
    
    add_contact_info();
}

sub process_email_servers {

    my ($num, $host, $port, $preference) = @_;
            
    error_out("Invalid host.") if not $antispam->check_hostname_syntax($host);
    error_out("Invalid port.") if not $antispam->check_port_syntax($port);
    error_out("Invalid preference.") if $preference and not $antispam->check_preference_syntax($preference);

    store_value('sd_host_'.$num, $host); 
    store_value('sd_port_'.$num, $port);
    store_value('sd_preference_'.$num, $preference);
}


############################### CONTACT INFO ###################################

sub add_contact_info {

    my (%HTML, $contact_id, @html_contacts, $contacts, %contact_list );

    # If contact id is hard coded in the config file, get it and go straight to confirmation.
    if ($contact_id = lookup_value('dflt_contact_id')) {
        store_value('sd_contact_id',lookup_value('dflt_contact_id'));
	confirm_new_purchase_order();
	
    # Otherwise get all user contacts for drop down list and
    # also show form for contact input.
    } else {

	my $result = $antispam->get_contacts_by_user_id(lookup_value('sd_domain_user_id'));
	error_out($result->{response_text}) if not $result->{is_success};
 
	map { 
	    $contact_list{$_->{contact_id}} = $_->{first_name}.", ".$_->{last_name}.", ".$_->{email}.", ".$_->{contact_id};
	} @{$result->{attributes}{result}};
	$contact_list{select} = "Please select Contact";

	$HTML{domain_name} = lookup_curr_domain_value('domain_name');
	$HTML{country_menu} = build_country_list();
	$HTML{contact_list} = build_select_menu(\%contact_list,'select' );

	print_form(template => "$path_templates/add_contact_info.html", data => \%HTML );
    }
}

sub edit_contact_info {

    my (%HTML, @key, @value);

    $HTML{domain_name} = lookup_curr_domain_value('domain_name');
    my $admin_contacts = lookup_value('sd_admin_contacts');

    map { @key=keys %{$_}; @value=values %{$_}; $HTML{@key[0]} = @value[0]} @{$admin_contacts};
    
    $HTML{country_menu} = build_country_list($HTML{country});    
    $HTML{edit_path} = 1;
    print_form(template => "$path_templates/add_contact_info.html", data => \%HTML );
}

sub do_add_contact_info {    

    confirm_new_purchase_order() if $in{cancel};

    # If user selected one of the existing contacts, get its id.
    if ( $in{admin_contact} and $in{admin_contact} ne 'select' ) {
        store_value('sd_contact_id',$in{admin_contact});
    # Otherwise get contact info from the form.     
    } else {
        my (@admin_contacts, $error, $full_key);
	my $contact_data = {};
	
        foreach ( qw(first_name last_name address1 city state country postal_code phone email) ) {

	    next if not $in{$_};
            $full_key = ( $_ =~ /^owner_/ ) ? $_ : 'owner_'.$_;
            $contact_data->{$full_key} = $in{$_};
	    push @admin_contacts, {$_ => $in{$_} };      
        }  

	my $result = $antispam->validate_contacts( $contact_data );

        error_out($result->{error}) if not $result->{is_success};
        store_value('sd_admin_contacts', \@admin_contacts);
    }
    confirm_new_purchase_order();
}


############################ CANCEL ORDER #############################################
sub cancel_new_purchase_order {

    print_form(template => "$path_templates/cancel_new_purchase_order.html");
    exit;

}

sub cancel_emaildefense_service {

    my %HTML;
    
    get_current_domain_info() if $in{init_curr_domain};
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    $HTML{domain_name} = $curr_domain_info->{domain_name};
    
    print_form(template => "$path_templates/cancel_emaildefense_service.html", data => \%HTML );

}
sub do_cancel_emaildefense_service {
    
    keep_emaildefense_service() if $in{keep_emaildefense_service};
    
    my %HTML;
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    # we need these values when returning to the manage domains page
    # to retrieve info for the user or domain.
    $HTML{domain_name} = $curr_domain_info->{domain_name};
    $HTML{domain_user_id} = $curr_domain_info->{domain_user_id};
    
    my $inventory_item_id = $curr_domain_info->{inventory_item_id};
    
    my $result = $antispam->tpp_cancel_emaildefense_service($inventory_item_id);
    
    error_out($result->{response_text}) if not $result->{is_success};
    
    print_form(template => "$path_templates/do_cancel_emaildefense_service.html", data => \%HTML );
}

sub keep_emaildefense_service {
    print_form(template => "$path_templates/keep_emaildefense_service.html");
    exit;
}


########################## CONFIRM ORDER ###############################################
sub confirm_new_purchase_order {

    my (%HTML, @key, @value);

    $HTML{allow_edit_contact} = lookup_value('sd_contact_id') ? 0 : 1;
 		    
    my $admin_contacts = lookup_value('sd_admin_contacts');

    map { @key=keys %{$_}; @value=values %{$_}; $HTML{@key[0]} = @value[0]} @{$admin_contacts};
    $HTML{cc_fields} = $antispam->cc_fields("$path_templates/cc_fields.html") if $ANTISPAM{F_SHOW_CC_FIELDS};
    confirm_order("confirm_new_purchase_order.html", \%HTML);   
    exit; 

}

sub confirm_add_manage_order {

    my %HTML;
    $HTML{cc_fields} = $antispam->cc_fields("$path_templates/cc_fields.html") if $ANTISPAM{F_SHOW_CC_FIELDS};

    confirm_order("confirm_add_manage_order.html", \%HTML);
}

sub confirm_remove_manage_order {

    confirm_order("confirm_remove_manage_order.html");
}

sub confirm_order {

    my %HTML;
    
    my $template = shift;
    my $HTML = shift;

    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    if (not $in{cancel}) {
        $curr_domain_info->{mod_user_accounts_string} = $curr_domain_info->{probable_mod_user_accounts_string};
	$curr_domain_info->{mod_user_accounts} = $curr_domain_info->{probable_mod_user_accounts};
	    }
    
    $HTML->{mod_user_accounts} = join ("<br>", @{$curr_domain_info->{mod_user_accounts_string}});
    $HTML->{mod_user_accounts_num} = scalar @{$curr_domain_info->{mod_user_accounts_string}};
    $HTML->{domain_name} = $curr_domain_info->{domain_name};
    $HTML->{new_purchase} = ( lookup_curr_domain_value('service_type') eq 'new_purchase' ) ? 1 : 0;

    if (scalar @{$curr_domain_info->{mod_user_accounts_string}}) {
        $HTML->{allow_process} = 1;
    }
        
    print_form(template => "$path_templates/$template", data => $HTML );

}

###################################### PROCESS ORDER ######################################

sub process_new_purchase_order {
    
    cancel_new_purchase_order() if $in{cancel_new_purchase_order};
    process_cc_fields() if $ANTISPAM{F_VERIFY_CC};
    
    my $order_info = get_new_purchase_order_info();
    
    my $result = $antispam->process_new_purchase_order($ANTISPAM{process_immediate}, $order_info);

    if ($result->{is_success}) { 
        $result->{html_action} = "new_purchase";       
        show_order_results($result);
    } else {
        error_out("$result->{attributes}{create_items}[0]{major_text}: $result->{response_text} ");
    }
}

sub process_add_manage_order {
    
    process_cc_fields() if $ANTISPAM{F_VERIFY_CC};
    
    my $order_info = get_add_manage_order_info();
    
    my $result = $antispam->process_upgrade_order($ANTISPAM{process_immediate}, $order_info);

    if ($result->{is_success}) {
        $result->{html_action} = "upgrade";       
        show_order_results($result);        
    } else {
        error_out("$result->{attributes}{create_items}[0]{major_text}: $result->{response_text} ");
    }
}

sub process_remove_manage_order {

    my $order_info = get_remove_manage_order_info();
    
    my $result = $antispam->process_downgrade_order($ANTISPAM{process_immediate}, $order_info);

    if ($result->{is_success}) {
        $result->{html_action} = "downgrade";       
        show_order_results($result);        
    } else {
        error_out("$result->{attributes}{create_items}[0]{major_text}: $result->{response_text} ");
    }
}

sub process_cc_fields {

    my %data = ( 
        p_cc_num => $in{p_cc_num},
	p_cc_type => $in{p_cc_type},
	p_cc_exp_mon => $in{p_cc_exp_mon},
	p_cc_exp_yr => $in{p_cc_exp_yr}    
    );
    
    my $result = $antispam->verify_cc_fields(\%data);	
        
    error_out($result->{error}) if not $result->{is_success};
    
    my $response = call_payment_gateway(\%data);
    
    if ( not call_payment_gateway(\%data) ) {
        error_out ("Credit Card information is not valid.");
    }
}
# For a reseller to enter payment gateway (credit card clearing) code.
sub call_payment_gateway {

    my $data = shift;
    
    # INSERT PAYMENT GATEWAY CODE HERE
    
    return 1;
}

##################################### GET ORDER INFO #################################

sub get_new_purchase_order_info {

    my (%order_info, $i, $server_info, @mtas, $entry);
       
    $order_info{user_id} = lookup_value('sd_domain_user_id');
    $order_info{domain_name} = lookup_curr_domain_value('domain_name');    
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    if ( lookup_value('sd_contact_id') ) {
	@{$order_info{admin_contacts}} = ( {id => lookup_value('sd_contact_id')} );
    } else {    
        $order_info{admin_contacts} = lookup_value('sd_admin_contacts');
    }        
    
    $i=1;
    while( lookup_value('sd_host_'.$i) ) {
    
        push @mtas, { host => lookup_value('sd_host_'.$i), 
		      port => lookup_value('sd_port_'.$i), 
		      preference => lookup_value('sd_preference_'.$i),
		    };
	$i++;
    }    
    $order_info{mtas} = \@mtas;
    
    my $mod_user_accounts = $curr_domain_info->{mod_user_accounts};   

    $i=0;
    foreach $entry (@{$mod_user_accounts}) {
	$order_info{create_items}[$i]{role} = $entry->{user_role};
	$order_info{create_items}[$i]{name} = $entry->{user_account};
	$order_info{create_items}[$i]{password} = $entry->{password};
		
	$i++;	
    }
    
    return \%order_info;  
}    

sub get_add_manage_order_info {

    my (%order_info, $i, $entry);
    
    @{$order_info{mod_user_accounts}} = ();
      
    $order_info{user_id} = lookup_value('sd_domain_user_id');
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    $order_info{inventory_item_id} = $curr_domain_info->{inventory_item_id};
    
    my $old_user_accounts = $curr_domain_info->{old_user_accounts};
    my $mod_user_accounts = $curr_domain_info->{mod_user_accounts};   
    
    $i=0;    
    foreach $entry (@{$old_user_accounts}) {
        $order_info{old_user_accounts}[$i]{role} = $entry->{role};
	$order_info{old_user_accounts}[$i]{name} = $entry->{name};
	$i++;	    
    }
    
    $i=0;
    foreach $entry (@{$mod_user_accounts}) {    
        $order_info{mod_user_accounts}[$i]{role} = $entry->{user_role};
	$order_info{mod_user_accounts}[$i]{name} = $entry->{user_account};			    
	$order_info{mod_user_accounts}[$i]{password} = $entry->{password};
	$i++;	
    }
            
    return \%order_info;  
}



sub get_remove_manage_order_info {

    my (%order_info, $i, $entry);
    
    $order_info{user_id} = lookup_value('sd_domain_user_id');
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
    
    $order_info{inventory_item_id} = $curr_domain_info->{inventory_item_id};
        
    my $old_user_accounts_string = $curr_domain_info->{old_user_accounts_string};
    my $mod_user_accounts_string = $curr_domain_info->{mod_user_accounts_string};
    
    @{$order_info{remained_user_accounts}} = ();
    foreach $entry (@{$old_user_accounts_string}) {
        ( push @{$order_info{remained_user_accounts}}, { name => $entry } ) 
	    if not grep /^$entry$/, @{$mod_user_accounts_string};
    }
    
    @{$order_info{mod_user_accounts_string}} = ();
    foreach $entry (@{$mod_user_accounts_string}) {
        push @{$order_info{mod_user_accounts_string}}, { name => $entry };	    
    }
        
    return \%order_info;  
}



########################### SHOW RESULTS ######################################

sub show_order_results {

    my (%HTML);
    
    my $data = shift;
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');    
    
    $HTML{reseller_email} = $ANTISPAM{reseller_email};
    $HTML{order_id} = $data->{attributes}{order_id};
    $HTML{domain_name} = $curr_domain_info->{domain_name};
        
    $HTML{action} = $data->{html_action};
    $HTML{new_purchase} = ( lookup_curr_domain_value('service_type') eq 'new_purchase' ) ? 1 : 0;
    $HTML{users} = scalar @{$curr_domain_info->{mod_user_accounts_string}};
    
    $HTML{ed_portal_url} = $ANTISPAM{ed_portal_url}; 

    print_form(template => "$path_templates/order_results.html", data => \%HTML );
}


################################ LIST FEATURES AND USERS ##################################
sub list_features_and_users {

    my (%HTML, @user_accounts);
    
    get_current_domain_info() if $in{init_curr_domain};    
    
    my $curr_domain_info = lookup_value('sd_curr_domain_info');
        
    $HTML{domain_name} = $curr_domain_info->{domain_name};
    $HTML{user_accounts} = join "<br>", @{$curr_domain_info->{old_user_accounts_string}};
    $HTML{num_user_accounts} = scalar @{$curr_domain_info->{old_user_accounts_string}};
        
    print_form(template => "$path_templates/list_features_and_users.html", data => \%HTML );
}

##########################################################################
# substitute values on the specified template and print it to the client

# an optional 'type' arg can be passed: 'framed' specifies to pull in base.html
# as the outer frame and the given template as the inner frame
# 'single' specifies to use the given template alone
# the default behavior is 'framed'
sub print_form {
    my %args = @_;
    
    $args{title} = "EmailDefense Registration/Management" if not $args{title};
    $args{username} = lookup_value('sd_username');
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

sub set_debugging_level {

    if ($ANTISPAM{debug}) {
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
