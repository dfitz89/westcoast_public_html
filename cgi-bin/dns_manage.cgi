#!/usr/local/bin/perl
#       .Copyright (C)  2002 TUCOWS.com Inc.
#       .Created:       2003/10/30
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://opensrs.org
#       .Authors:       Vedran Vego
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

# $Id: dns_manage.cgi,v 1.15 2005/09/02 23:01:23 ygumerova Exp $

use vars qw(
    %in $cgi $path_templates %actions $action $TPP_Client 
    $user_id $user_name $COOKIE_NAME $flag_header_sent %cookies 
    $error_msg $info_msg $path_to_config
);

# Null these things out for mod_perl users
(%in, $cgi, $path_templates, %actions, $action,
 $TPP_Client, $info_msg, $error_msg, $path_to_config) = ();


# pull in conf file with defined values
BEGIN {
    $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";

    # first "do" the major config file
    do "$path_to_config/OpenSRS.conf";

    # now load up the config for Dns service
    do "$path_to_config/Dns_manage.conf";
}

use strict;
use lib $PATH_LIB;

use CGI ':cgi-lib';
use HTML::Template;
use Data::Dumper;
use Core::Checksum qw(calculate compare);
use OpenSRS::TPP_Client;
use OpenSRS::ResponseConverter;
use OpenSRS::Util::ConfigJar "$path_to_config/OpenSRS.conf";
use OpenSRS::Util::Common qw(make_navbar_dns);

# global defines
$user_id = 0;
$user_name = '';
$COOKIE_NAME = "OPENSRS_TPP_CLIENT";
$flag_header_sent = 0;
$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/dns_manage";
%in = ();
$error_msg = '';
$info_msg = '';

# list of valid actions to execute
%actions = (
    login => undef,
    do_login => undef,
    main => undef,
    dns_list_inventory_items => undef,
    dns_manage_zone => undef,
    dns_manage_domain_forwarding => undef,
    dns_do_update_zone => undef,
    dns_update_domain_forwarding => undef,
    dns_retrieve_zone => undef,
    dns_restore_zone_defaults => undef,
    edit_for_sale_template => undef,
    update_for_sale_template => undef,
    logout => undef,
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
    exit;
}

# close connection to the server
$TPP_Client->logout;

exit;

##########################################################################

sub start_up {
    if ($DNS_MANAGE{debug}) {
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
    
    $args{title} = $args{title} || 'DNS Service Management';
    
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

    if ($cookies{user_name}) {
       $user_name = $cookies{user_name};
    }

    return $ok;
}                                                                           

sub login {
    my $error_message = shift;
    
    my %HTML = ();
    $HTML{error_message} = $error_message;
    $HTML{cgi} = $cgi;
    $HTML{username} = $in{username} if $in{username};
    $HTML{title} = "DNS Service Management";
    $HTML{password_recovery} = $DNS_MANAGE{password_recovery};

    print_form(template => "$path_templates/login.html", data => \%HTML);
}

sub do_login {
    my $result;

    if (not $in{username} or not $in{password}) {
	login('Authentication failed.');
	return;
    }

    # check if user exists
    $result = $TPP_Client->login_user(
        $in{username}, $in{password}, $OPENSRS{username}
    );
    
    if (not defined $result or not $result->{is_success}) {
	my $err = sprintf 'Failed to authenticate user: %s',
	    $result->{response_text} || 'Empty response from server';
	login($err);
	return;
    }

    $user_id = $result->{attributes}{user_id};
    if (not $user_id) {
	login('Unable to get user ID.');
	return;
    }
    
    # sign user_id and set the cooke.
    my $csum = calculate($OPENSRS{private_key}, $user_id);
    print_header($COOKIE_NAME => "$csum:$user_id", user_name => $in{username});
    $user_name = $in{username};

    main();
}

sub logout {
    # reset global user_id and a cookie
    $user_id = 0;
    print_header($COOKIE_NAME => '', user_name => '');
    login();
}

##########################################################################

sub main {    
    dns_list_inventory_items();
}

sub get_inventory_items {

    my ($start_page,$page_size) = @_;
    my $start_index = ($start_page * $page_size) + 1;

    my $TPP_request = {
         protocol => 'TPP',
         version => '1.3.0',
         action => 'execute',
         object => 'query',
         requestor => {
             username => $OPENSRS{username},
         },
         attributes => {
	     user_id => $user_id,
             page_size => $page_size,          
             start_index => $start_index,
             query_name => 'inventory_items.created.by_user_id',
             conditions => [
                 {
                     type => 'simple',
                     field => 'user_id',
                     operand => {
                         'eq' => $user_id,
                     },
                 },
                 {
                     type => 'link',
                     link => 'and',
                 },
                 {
                     type => 'simple',
                     field => 'service',
                     operand => {
                         'eq' => 'dns',
                     },
                 },
             ],
 
         }
    };  

    my $TPP_response =
       $TPP_Client->send_cmd($TPP_request);
    if ( not $TPP_response->{is_success}) {
        error_out('Unable to retrieve products: ' .
                   $TPP_response->{response_text});
        exit;
    }

    return ($TPP_response->{attributes}{result},
            $TPP_response->{attributes}{result_control}{record_count});
}

sub dns_list_inventory_items {

    my %HTML = ();
    my $page = $in{page} || 0;
    my $limit = 20;

    my ($items, $total_records) = get_inventory_items($page,$limit);
    $items = [ grep $_->{service} eq 'dns',  @{$items} ];

    my $counter = 0;
    foreach my $item (@{$items}) {
        $item->{class} = $counter++ % 2 ? "accent" : "soft";
        $item->{object_type} = ucfirst $item->{object_type}." DNS";
        $item->{creation_date} = (split(/\s/,$item->{creation_date}))[0];
        $item->{cgi} = $cgi;
    }

    my $num_page_links = 10;
    my $f_navpage = make_navbar_dns(
                    "dns_list_inventory_items",
                    $total_records, $limit, 
                    $num_page_links, $page
    );
   
    my @f_navbar = (
                      {
                        external => 1,
                        title => 'PASSWORD MANAGEMENT',
                        action => $DNS_MANAGE{password_url},
                        separator => ' | ',
                        target => qw (target="blank_"),
                      },
                      {
                        cgi => $cgi."?",
                        title => 'ZONE LIST',
                        action => 'dns_list_inventory_items',
                        separator => ' | ',
                      },
                      {
                        cgi => $cgi."?",
                        title => 'LOGOUT',
                        action => 'logout',
                        separator => '',
                      }
                    );  
                                 
    $HTML{total_records} = $total_records;                         
    $HTML{records} = $items;
    $HTML{page} = $page;
    $HTML{limit} = $limit;
    $HTML{cgi} = $cgi;

    $HTML{f_navpage} = $f_navpage;
    $HTML{f_navbar} = \@f_navbar;
    $HTML{f_title} = "DNS Management";
    $HTML{f_name} = $user_name;
    $HTML{stat_message} = "<font color=\"red\">".$error_msg ."</font>"."<font color=\"green\">". $info_msg."</font>";

    $HTML{title} = $HTML{f_title};
    print_form(template => "$path_templates/main.html", data => \%HTML);
}

sub get_inventory_item {

    my $inventory_item_id = shift;

    my $TPP_request = {
        protocol => 'TPP',
        version => '1.3.0',
        action => 'execute',
        object => 'query',
        requestor => {
             username => $OPENSRS{username},
        }, 
        attributes => {
	    user_id => $user_id, 
            query_name => 'inventory_item.by_id',
            conditions => [
                {
                    type => 'simple',
                    field => 'inventory_item_id',
                    operand => {
                        'eq' => $inventory_item_id,
                    },
                },
            ],
        },
    };

    my $TPP_response = 
       $TPP_Client->send_cmd($TPP_request);
    if ( not $TPP_response->{is_success} ||
        !(defined $TPP_response->{attributes}->{result}->[0])) 
    {
        error_out('Unable to query product: ' . 
                   $TPP_response->{response_text});
        exit;
    }

    return $TPP_response->{attributes}->{result}->[0];
}

sub relativename_to_fullname {
  my $zone_data = shift;
  
  my $zone_name = $zone_data->{name};
  
  foreach my $zone_record (@{ $zone_data->{records} }) {
    if (($zone_record->{type} =~ /^(CNAME|MX|NS)$/i) and
       ($zone_record->{content} !~ /^\s*$/ )) {
       $zone_record->{content} .= '.'.$zone_name unless
           $zone_record->{content} =~ /\.$/;
    }
  }  
}

sub dns_manage_zone {

    # when dns_do_update_zone() calls dns_manage_zone() it might pass
    # zone update result
    my $zone_update_result = shift;

    my %HTML = ();
    $HTML{cgi} = $cgi;

    unless ( $in{inventory_item_id}) {
        error_out('Inventory item id must be specified');
        exit;
    }

    my $inventory_item = get_inventory_item($in{inventory_item_id});
    if (not $inventory_item) {
        error_out('Null inventory_item in response');
        exit;
    }

    if ( !validate_item_action($inventory_item->{product_data}{flags},'zone')) {
       add_info_message("Zone management permission is currently disabled for this zone.");
       return main();
    }

    my $dns_zone = $inventory_item->{product_data}{zone_data};
    relativename_to_fullname($dns_zone);
    if (not defined $dns_zone) {
        error_out('Null zone_data in response');
        exit;
    }

    # if we were given a $zone_update_result:
    # set error header and extract update results
    my $delete_results = [];
    my $create_results = [];
    my $update_results = [];
    if (defined $zone_update_result) {
        $delete_results = $zone_update_result->{delete_records};
        $create_results = $zone_update_result->{create_records};
        $update_results = $zone_update_result->{update_records};
    }

    my $records = $dns_zone->{records};
    my $zone_fqdn = $dns_zone->{name};

    $HTML{stat_message} = "<font color=\"red\">".$error_msg ."</font>"."<font color=\"green\">". $info_msg."</font>";
    $HTML{inventory_item_id} = $in{inventory_item_id};
    
    $HTML{version} = $dns_zone->{version};
    $HTML{zone_fqdn} = $zone_fqdn;
    $HTML{a_records} =  build_records($in{inventory_item_id},
	$zone_fqdn, $delete_results, $update_results, $records,'A');
	    
    $HTML{cname_records} = build_records($in{inventory_item_id}, $zone_fqdn,
	$delete_results, $update_results, $records, 'CNAME');

    $HTML{txt_records} = build_records($in{inventory_item_id}, $zone_fqdn,
        $delete_results, $update_results, $records, 'TXT');
	
    $HTML{mx_records} = build_records($in{inventory_item_id}, $zone_fqdn,
	$delete_results, $update_results, $records, 'MX');
	
    $HTML{ns_records} = build_records($in{inventory_item_id}, $zone_fqdn,
	$delete_results, $update_results, $records, 'NS');
	
    $HTML{a_records_add} = build_add_records($zone_fqdn, $create_results, 'A');
    
    $HTML{cname_records_add} =
        build_add_records($zone_fqdn,$create_results,'CNAME');

    $HTML{txt_records_add} =
        build_add_records($zone_fqdn,$create_results,'TXT');

    $HTML{mx_records_add} =
        build_add_records($zone_fqdn,$create_results,'MX');

    $HTML{ns_records_add} =
        build_add_records($zone_fqdn, $create_results,'NS');
    $HTML{ids} = join(',', map { $_->{id} } @{$records});

    $HTML{f_title} = "Zone Management: $zone_fqdn";
    $HTML{f_name} = $zone_fqdn;
    
    my @f_navbar = (
                     {
                       cgi => $cgi."?",
                       title => 'ZONE LIST',
                       action => 'dns_list_inventory_items',
		       separator => ' | ',	
                     },
                     {
                       cgi => $cgi."?",
                       title => 'LOGOUT',
                       action => 'logout',
                       separator => '',
                     }
                   );

    $HTML{f_navbar} = \@f_navbar;

    $HTML{title} = $HTML{f_title};
    
    print_form(template => "$path_templates/dns_manage_zone.html", data => \%HTML);  
}

sub build_records {
 
    my ($inventory_item_id, $zone_fqdn,
	$delete_results, $update_results,
	$in_records, $type) = @_;

    my $records = [ grep $_->{type} eq $type, @{$in_records} ];
    my %deleted = map { $_->{id} => 1 } @{$delete_results};
    my %updated = map { $_->{id} => $_ } @{$update_results};
 
    my @html_records = ();
    my %name_map = ();
    foreach my $record (@{$records}) {
        my $name = $record->{name};
        if ($name_map{$name}) {
            push @{$name_map{$name}}, $record;
        } else {
            $name_map{$name} = [ $record ];
        }
    }
 
    my $counter = 0;
    foreach my $name (keys %name_map) {
       my $name_records = $name_map{$name};
       my $num = scalar @{$name_records};
       my $rowspan = $num > 1 ? "valign=top rowspan=$num" : "";
 
       my $first_row = 1;
       foreach my $record (@{$name_records}) {
          my $id = $record->{id};
          if (defined $updated{$id}) {
              map {
                $record->{$_} = $updated{$id}->{$_}
              } keys %{ $updated{$id} };
          }
 
          my $error = '';
          if (defined $record->{response_code} and
              $record->{response_code} != 200 and
              $record->{response_text}) {
              $error = $record->{response_text};
          }

          my $rec_name;
          if ($first_row) {
              $rec_name = $name eq '@' ? $zone_fqdn : "$name.$zone_fqdn";
              $first_row = 0;
          }
 
          push(@html_records,
               {
	         inventory_item_id => $inventory_item_id,
                 id => $id,
                 error => $error,
                 class => $counter++ % 2 ? "accent" : "soft",
                 rec_name => $rec_name,
                 name => $name,
                 type => $record->{type},
                 content => $record->{content},
                 priority => $record->{priority},
                 delete_checked => $deleted{$id} ? "checked" : '',  
                 rowspan => $rowspan,
                 read_only => $record->{read_only}, 
               }
          ); 
       }
    }
 
    return \@html_records;  
}
 
sub build_add_records {
    my ($zone_fqdn, $create_results, $type) = @_;
 
    my $created = [];    
    foreach my $result (grep { $_->{type} eq $type } @{$create_results}) {
	if ($_->{name} eq '@') {
	    unshift @{$created}, $result;
	} else {
	    push @{$created}, $result;
	}
    }
 
    my @html_add_records = ();
    my $counter = 0;
    for (my $i = 0; $i < $DNS_MANAGE{bulk_factor}; $i++) {
	my $suffix = 'new_' . $i . '_' . $type;
	my $create_record = {};
	if (($type == 'MX' || $type == 'A') and $i == 0) {
	    if ($created->[0]->{name} eq '@') {
		$create_record = shift @{$created};
	    } else {
		$create_record = {};
	    }
	} else {
	    $create_record = (shift @{$created}) || {};
	}
	 
         if ($create_record->{name} eq '@') {
             $create_record->{name} = '';
         }
       
         my $error = '';
         if (defined $create_record->{response_code} and
             $create_record->{response_code} != 200 and
             $create_record->{response_text}) {
             $error = $create_record->{response_text};
         }
 
         push(@html_add_records,
              {
                error => $error,
                class => $counter++ % 2 ? "accent" : "soft",
                suffix => $suffix,
                name => $create_record->{name},
                priority => $create_record->{priority},
                content => $create_record->{content},
                zone_fqdn => $zone_fqdn,
                is_input_hidden => ($i == 0 and ($type == 'MX' || $type == 'A')) ?
                    1 : 0
              }
         );
    }
 
    return \@html_add_records;  
}         

sub dns_do_update_zone {

    my $TPP_request = {
        version => '1.4.0',
        action => 'update',
        object => 'inventory_item.dns',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
            service => 'dns',
	    user_id => $user_id,
            inventory_item_id => $in{inventory_item_id},
            product_data => {
                zone => {
                    version => $in{version},
                    %{ parse_update_zone_records_request() },
                },
            },
        },
    };

    my $TPP_response = $TPP_Client->send_cmd($TPP_request);

    my $zone_update_result;
    if (not $TPP_response->{is_success}) {
	if ($TPP_response->{response_code} == 31472) {
	    add_error_message(
		"Zone record entry error"
	    );
	} else {
	    add_error_message($TPP_response->{response_text});
	}
        $zone_update_result = $TPP_response->{attributes}{product_data}{zone};
    } else {
        add_info_message($TPP_response->{response_text});
    }

    return dns_manage_zone($zone_update_result);
}

sub dns_restore_zone_defaults {

    my $delete_records = [];
    if ($in{ids}) {
        map {
            push @{$delete_records}, { id => $_ };
        } split /,/, $in{ids};
    }

    my $TPP_request = {
        version => '1.4.0',
        action => 'update',
        object => 'inventory_item.dns',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
	    user_id => $user_id,
            service => 'dns',
            inventory_item_id => $in{inventory_item_id},
            product_data => {
                zone => {
                    version => $in{version},
                    delete_records => $delete_records,
                    create_records => [],
                    update_records => [],
                },
                template => {
                    name => 'default',
                },
            },
        },
    };

    my $TPP_response = $TPP_Client->send_cmd($TPP_request);
    if ($TPP_response->{is_success}) {
        add_info_message($TPP_response->{response_text});
    } else {
        add_error_message($TPP_response->{response_text});
    }

    dns_manage_zone();
}

sub dns_retrieve_zone {

    error_log('Inventory item id must be specified')
        unless $in{inventory_item_id};

    my $inventory_item = get_inventory_item($in{inventory_item_id});
    if (not $inventory_item) {
        add_error_message('Null inventory_item in response');
    }

    my $dns_zone = $inventory_item->{product_data}{zone_data};
    if (not defined $dns_zone) {
        add_error_message('Null zone_data in response');
    }

    my $zone_records = $dns_zone->{records} || [];
    my $retrieved_records = [];
    my $TPP_response = retrieve_zone_records($dns_zone->{name});
    if (not $TPP_response->{is_success}) {
        add_error_message($TPP_response->{response_text});
        return dns_manage_zone();
    } else {
        $retrieved_records =
            $TPP_response->{attributes}{product_data}{zone}{records};
    }

    my $TPP_request = {
        version => '1.4.0',
        action => 'update',
        object => 'inventory_item.dns',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
            service => 'dns',
	    user_id => $user_id,
            inventory_item_id => $in{inventory_item_id},
            product_data => {
                zone => {
                    version => $in{version},
                    delete_records => $in{replace} ? $zone_records : [],
                    create_records => $retrieved_records,
                    update_records => [],
                },
            },
        },
    };

    $TPP_response = $TPP_Client->send_cmd($TPP_request);
    if ($TPP_response->{is_success}) {
        add_info_message($TPP_response->{response_text});
    } else {
        add_error_message($TPP_response->{response_text});
    }

    dns_manage_zone();
}

sub retrieve_zone_records {
   
    my $fqdn = shift;
    my $prefixes = shift;

    my $TPP_request = {
        action => 'retrieve',
        object => 'dns.zone',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
            service => 'dns',
	    user_id => $user_id,
            product_data => {
                zone => {
                    name => $fqdn,
                },
                prefixes => $prefixes || [],
            },
        },
    };

    my $TPP_response = $TPP_Client->send_cmd($TPP_request);

    return $TPP_response;
}

sub parse_update_zone_records_request {

    my $delete_records = [];
    if ($in{delete_records}) {
        foreach (split /\0/,$in{delete_records}) {
            push @{$delete_records}, { id => $_ };
        }
    }

    my %processed = ();
    my $update_records = [];
    foreach my $orig_entity (keys %in) {
        my ($suffix) = $orig_entity =~ /(\d+_orig)$/;
        next if (not $suffix or $processed{$suffix});

        my ($id) = $suffix =~ /(\d+)_orig$/;

        my $update_record;
        my @entities = grep /$suffix$/, keys %in;
        foreach my $entity (@entities) {
            my ($updated_entity) = $entity =~ /^(.+_\d+)_orig$/;
            if ($in{$entity} !~ /^\s*$/ and $in{$entity} ne $in{$updated_entity}) {
                if (not defined $update_record) {
                    $update_record = {id => $id};
                }
                my ($entity_name) = $updated_entity =~ /^(.+)_\d+$/;
                $update_record->{$entity_name} = $in{$updated_entity};
            }
        }



	if (defined $update_record) {
	    if (exists $update_record->{content} and
		$update_record->{content} !~ /^\s*$/) {

		my $type = $in{'type_' . $update_record->{id}};
		if ($type ne 'A' and $update_record->{content} !~ m/\.$/) {
		    $update_record->{content} .= '.';
		}
            }
	    push @{$update_records}, $update_record;
	}
	
	$processed{$suffix} = 1;
    }

    my $create_records = [];
    if ($in{suffix}) {
        foreach my $suffix (split /\0/, $in{suffix}) {
            my ($type) = $suffix =~ /\d+_(.+)$/;
            my $create_record = {type => $type};
            map {
                $_ =~ /^(.+)_$suffix$/;
                if ($in{$_} !~ /^\s*$/) {
                    $create_record->{$1} = $in{$_};
                }
            } grep /$suffix$/, keys %in;

            if (not $create_record->{name}) {
                $create_record->{name} = '@';
            }

            if (scalar keys %{$create_record} > 2) {
                if (exists $create_record->{content} and
                    $create_record->{type} =~ m/^(CNAME|MX|NS)$/i) {
                  $create_record->{content} .= '.' unless
                    $create_record->{content} =~ m/\.$/;
                }

                push @{$create_records}, $create_record;
            }
        }
    }

    return {
        delete_records => $delete_records,
        create_records => $create_records,
        update_records => $update_records,
    };
}

sub dns_manage_domain_forwarding {
    # when dns_update_domain_forwarding() calls dns_manage_domain_forwarding()
    # it might pass update result
    my $update_result = shift;        

    my %HTML = ();
    $HTML{cgi} = $cgi;

    unless ( $in{inventory_item_id} ) {
        error_out('Inventory item id must be specified');
        exit;
    }

    my $inventory_item = get_inventory_item($in{inventory_item_id});

    if (not $inventory_item) {
        error_out('Null inventory_item in response');
        exit;
    }

    if ( !validate_item_action($inventory_item->{product_data}{flags},'forwarding')) {
       add_info_message("Domain forwarding permission is currently disabled for this zone.");
       return main();
    }

    my $zone_data = $inventory_item->{product_data}{zone_data};
    if (not defined $zone_data) {
        error_out('Null zone_data in response');
        exit;
    }

    my $zone_services = $inventory_item->{product_data}{zone_services};
    if (not defined $zone_services) {
        error_out('Null zone_services in response');
    }

    # if we were given a $update_result - extract update results
    my $delete_results = [];
    my $create_results = [];
    my $update_results = [];
    if (defined $update_result) {
        $delete_results = $update_result->{delete_services};
        $create_results = $update_result->{create_services};
        $update_results = $update_result->{update_services};
    }

    # scan for 'www' zone service
    my $create_www = 1;
    map {
	$create_www = 0 if $_->{prefix} eq 'www'
    } @$zone_services;
    
    # scan for 'www' zone records
    if ($create_www) {
	map {
	    $create_www = 0 if $_->{name} eq 'www'
	} @{$zone_data->{records}};
    }
    $HTML{create_www} = $create_www;


    my $zone_fqdn = $zone_data->{name};

    $HTML{stat_message} = "<font color=\"red\">".$error_msg ."</font>"."<font color=\"green\">". $info_msg."</font>";
    $HTML{inventory_item_id} = $in{inventory_item_id};
    $HTML{zone_fqdn} = $zone_fqdn;
    $HTML{f_title} = "Domain Forwarding Management: $zone_fqdn";
    $HTML{f_name} = $zone_fqdn;

    $HTML{show_forwarding} = $inventory_item->{product_data}{flags}{allow_url_forwarding};
    $HTML{show_templates} = $inventory_item->{product_data}{flags}{allow_templates};

    # default
    $HTML{domain_setting} = "none";
    $HTML{chk_none} = "checked";
    $HTML{domain_cloak} = 0;
    $HTML{domain_url} = 'http://';

    my $zone_services_num = scalar @{$zone_services}; # this for subdomain
    foreach my $zone_service (@{$zone_services}) {
        next unless $zone_service->{prefix} eq "@";

       # do not count zone service for domain
       --$zone_services_num;
       $HTML{domain_zone_service_id} = $zone_service->{id};
       if ($zone_service->{type} eq 'template') {
           $HTML{chk_none} = "";
           if ($zone_service->{content} eq 'under-construction') {
               $HTML{domain_setting} = "uc";
               $HTML{chk_uc} = "checked";
           } elsif ($zone_service->{content} eq 'for-sale') {
              $HTML{domain_setting} = "fs";
              $HTML{chk_fs} = "checked";
           }
       } elsif ($zone_service->{type} eq 'url-cloak') {
           $HTML{domain_setting} = "fwd";
           $HTML{domain_url} = $zone_service->{content};
           $HTML{domain_cloak} = 1;
           $HTML{chk_none} = "";
           $HTML{chk_fwd} = "checked";
       } elsif ($zone_service->{type} eq 'redirector') {
           $HTML{domain_setting} = "fwd";
           $HTML{domain_url} = $zone_service->{content};
           $HTML{chk_none} = "";
           $HTML{chk_fwd} = "checked";
       }
 
       last;
    }

    $HTML{subdomain_forward_records} = 
          build_fw_records($zone_services,$zone_fqdn);
    $HTML{subdomain_forward_add_records} =
          build_fw_add_records($create_results, $zone_fqdn, $create_www);

    my @f_navbar = (
                     {
                       cgi => $cgi."?",
                       title => 'ZONE LIST',
                       action => 'dns_list_inventory_items',
                       separator => ' | ',
                     },
                     {
                       cgi => $cgi."?",
                       title => 'LOGOUT',
                       action => 'logout',
                       separator => '',
                     }
                   );
                                                                                                                                                                                                     
    $HTML{f_navbar} = \@f_navbar;
    $HTML{title} = $HTML{f_title};
    
    print_form(template => "$path_templates/dns_domain_forwarding.html", data => \%HTML);
}

sub build_fw_records {
    
    my ($zone_services,$zone_fqdn) = @_;
    my @html_fw_records;
   
    my $counter = 0;  
    foreach my $zone_service (@{$zone_services}) {
        next if $zone_service->{prefix} eq '@';
      
        push(@html_fw_records,
             { 
               class => $counter++ % 2 ? "accent" : "soft",
               prefix => $zone_service->{prefix},
	       name => $zone_fqdn,
               content => $zone_service->{content},
               id => $zone_service->{id},
               url_cloak => $zone_service->{type} eq "url-cloak" ? 1 : 0,
             }
        );
    }

    return \@html_fw_records;
}

sub build_fw_add_records {
    my ($create_results, $zone_fqdn, $create_www) = @_;
    my @html_fw_add_records;
    my $new_service = {};

    foreach my $create_result (@{$create_results}) {
        # skip create_result for domain
        next if $create_result->{prefix} eq '@';

	# XXX fix it to use resonse code
	if (not $create_result->{id}) {
	    # ignore auto-created forwarding for 'www' subdomain
	    next if $create_result->{prefix} eq 'www' and $create_www;
	    
	    $new_service = $create_result;
	    last;
	}
    }

    push(@html_fw_add_records,
         {
           class => "accent",
           new_subdomain => $new_service->{prefix},
           new_url => $new_service->{content} || 'http://',
           new_cloaked => $new_service->{type} eq 'url-cloak' ? "checked" : "",
           zone_fqdn => $zone_fqdn,
         }
    );

    return \@html_fw_add_records;
}

sub dns_update_domain_forwarding {

    my $update_data = parse_update_zone_services_request();

    if ($in{create_www} and $in{domain_setting} ne 'none') {
	# make sure there is no other 'www' domain forward to create
	my $www_exists = 0;
	map {
	    $www_exists = 1 if $_->{prefix} eq 'www'
	} @{$update_data->{create_services}};

	push @{$update_data->{create_services}}, {
	    prefix => 'www',
	    type => 'redirector',
	    content => "http://" . $in{create_www},
	} unless $www_exists;
    }

    if ( scalar @{$update_data->{delete_services}} == 0 && 
         scalar @{$update_data->{create_services}} == 0 && 
         scalar @{$update_data->{update_services}} == 0)  
    {
         return dns_manage_domain_forwarding();    
    }

    my $TPP_request = {
        version => '1.4.0',
        action => 'update',
        object => 'inventory_item.dns',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
	    user_id => $user_id,
            service => 'dns',
            inventory_item_id => $in{inventory_item_id},
            product_data => {
		zone_services => $update_data,
	    }
        },
    };

    my $TPP_response = $TPP_Client->send_cmd($TPP_request);

    my $update_result;
    if (not $TPP_response->{is_success}) {
        $update_result = $TPP_response->{attributes}{product_data}{zone_services};

        my $error_text;
        TYPE:
        foreach my $type qw(create_services delete_services update_services) {
            my @services = @{ $TPP_response->{attributes}{product_data}{zone_services}{$type} };
            foreach my $service (@services) {
                if ($service->{response_code} != 200 and
                        $service->{response_text}) {

                    if ($service->{prefix} ne '@') {
                        if ($type eq 'create_services') {
                            $error_text =
                                "Failed to create subdomain forwarding: ";
                        } elsif ($type eq 'delete_services') {
                            $error_text =
                                "Failed to delete subdomain forwarding: ";
                        } elsif ($type eq 'update_services') {
                            $error_text =
                                "Failed to update subdomain forwarding: ";
                        }
                    } else {
                        $error_text = "Failed to update domain forwarding: ";
                    }

		    if ($service->{response_code} == 30441) {
			# "Invalid zone service content"
			$error_text .= "Format of entry is invalid: " .
			    $service->{content};
		    } else {
			$error_text .= $service->{response_text};
		    }
                    last TYPE;
                }
            }
        }

        if ($error_text) {
            add_error_message($error_text);
        } else {
            add_error_message($TPP_response->{response_text});
        }
    } else {
        add_info_message($TPP_response->{response_text});
    }

    return dns_manage_domain_forwarding($update_result);
}

sub parse_update_zone_services_request {

    my $delete_services = [];
    my $create_services = [];
    my $update_services = [];

    # parse domain settings
    my $domain_zone_service_type;
    my $domain_zone_service_content;
    if ($in{domain_setting} eq 'uc') {
        $domain_zone_service_type = 'template';
        $domain_zone_service_content = 'under-construction';
    } elsif ($in{domain_setting} eq 'fs') {
        $domain_zone_service_type = 'template';
        $domain_zone_service_content = 'for-sale';
    } elsif ($in{domain_setting} eq 'fwd') {
        $in{domain_cloak} = 0 unless defined $in{domain_cloak};
        $domain_zone_service_type =
            $in{domain_cloak} ? 'url-cloak' : 'redirector';
        $domain_zone_service_content = $in{domain_url};
    }
    if ($in{domain_setting} ne $in{orig_domain_setting}) {
        my $tmp = $in{orig_domain_setting} . $in{domain_setting};
        if ($tmp eq 'fsuc' or $tmp eq 'ucfs') {
            push @{$update_services}, {
                id => $in{domain_zone_service_id},
                content => $domain_zone_service_content,
            };
        } else {
            if ($in{orig_domain_setting} ne 'none') {
                push @{$delete_services}, {
                    id => $in{domain_zone_service_id}
                };
            }
            if ($in{domain_setting} ne 'none') {
                push @{$create_services}, {
                    prefix => '@',
                    type => $domain_zone_service_type,
                    content => $domain_zone_service_content,
                };
            }
        }
    } elsif ($in{domain_setting} eq 'fwd') { 
	if ($in{domain_cloak} ne $in{orig_domain_cloak}) {
	    push @{$delete_services}, {
		id => $in{domain_zone_service_id},
	    };
	    push @{$create_services}, {
		prefix => '@',
		type => $domain_zone_service_type,
		content => $domain_zone_service_content,
	    };
	} elsif ($in{domain_url} ne $in{orig_domain_url}) {
	    push @{$update_services}, {
		id => $in{domain_zone_service_id},
		content => $domain_zone_service_content,
	    };
	}
    }

    # parse new subdomain
    if ($in{new_subdomain}) {
        push @{$create_services}, {
            prefix => $in{new_subdomain},
            type => $in{new_cloaked} ? 'url-cloak' : 'redirector',
            content => $in{new_url},
        };
    }

    # parse updates/deletions
    foreach my $key (keys %in) {
        if ($key =~ /^delete_(\d+)$/) {
            push @{$delete_services}, { id => $1 };
        } elsif ($key =~ /^url_(\d+)$/ ) {
       
	    next if defined $in{"delete_$1"};
       
	    if ($in{$key} ne $in{"orig_$key"}) {
	        push @{$update_services}, {
		    id => $1,
		    content => $in{$key},
	        };
	    }

	    $in{"subdomain_cloak_$1"} = 0 unless $in{"subdomain_cloak_$1"};

	    if ($in{"subdomain_cloak_$1"} ne $in{"orig_subdomain_cloak_$1"}) {
	        push @{$delete_services}, {  
		   id => $1,
	        };
	        push @{$create_services}, {
		    prefix => $in{"prefix_$1"},
		    type => $in{"subdomain_cloak_$1"} ? 'url-cloak' : 'redirector',
		    content =>  $in{"url_$1"},
	        };
	    }
 	}
    }
    # now check for services to be deleted, but that are in update list also
    # remove such services from update list
    my %delete_map = map { $_->{id} => undef } @$delete_services;
    my %update_map = map { $_->{id} => $_ } @$update_services;
    map { delete $update_map{$_} } keys %delete_map;
    $update_services = [ values %update_map ];

    return {
        delete_services => $delete_services,
        create_services => $create_services,
        update_services => $update_services,
    };
}

sub edit_for_sale_template {

    my %HTML = ();
    $HTML{cgi} = $cgi;

    unless ( $in{inventory_item_id} ) {
        error_out('Inventory item id must be specified');
        exit;
    }

    my $inventory_item = get_inventory_item($in{inventory_item_id});

    if (not $inventory_item) {
        error_out('Null inventory_item in response');
        exit;
    }

    my $zone_data = $inventory_item->{product_data}{zone_data};
    if (not defined $zone_data) {
        error_out('Null zone_data in response');
        exit;
    }

    my $zone_services = $inventory_item->{product_data}{zone_services};
    if (not defined $zone_services) {
        error_out('Null zone_services in response');
    }
      
    foreach my $zone_service (@{$zone_services}) {
        next unless $zone_service->{content} eq "for-sale" &&
                    $zone_service->{type} eq "template";

        $HTML{domain_zone_service_id} = $zone_service->{id};
        $HTML{heading} = $zone_service->{parameters}{heading};
        $HTML{description} = $zone_service->{parameters}{description};
    }

    $HTML{stat_message} = "<font color=\"red\">".$error_msg ."</font>"."<font color=\"green\">". $info_msg."</font>";
    $HTML{inventory_item_id} = $in{inventory_item_id};
    $HTML{zone_fqdn} = $zone_data->{name};
    $HTML{f_title} = "For Sale Template: ".$zone_data->{name};
    
    $HTML{title} = $HTML{f_title};
    print_form(template => "$path_templates/for_sale_template.html", data => \%HTML);
}

sub update_for_sale_template {

    if ( length($in{heading}) > 255) {
        add_error_message("Invalid number of characters for heading field [max 255]");
        return edit_for_sale_template();
    }
 
    if ( length($in{description}) > 3999) {
        add_error_message("Invalid number of characters for description field [max 3999]");
        return edit_for_sale_template();
    }
 
    my $update_data = parse_update_for_sale_template_request();

    if (scalar @{$update_data->{update_services}} == 0) {
         return edit_for_sale_template();
    }

    my $TPP_request = {
        version => '1.4.0',
        action => 'update',
        object => 'inventory_item.dns',
        requestor => {
            username => $OPENSRS{username},
        },
        attributes => {
	    user_id => $user_id,
            service => 'dns',
            inventory_item_id => $in{inventory_item_id},
            product_data => {
		zone_services => $update_data,
	    },
        },
    };

    my $TPP_response = $TPP_Client->send_cmd($TPP_request);

    if (not $TPP_response->{is_success}) {
        add_error_message($TPP_response->{response_text});
    } else {
        add_info_message($TPP_response->{response_text});
    }

    return edit_for_sale_template();
}

sub parse_update_for_sale_template_request {

    my $delete_services = [];
    my $create_services = [];
    my $update_services = [];

    push @{$update_services}, {
               id => $in{domain_zone_service_id},
               parameters => {
                   heading => $in{heading},
                   description => $in{description},
               }
           };

    return {
        delete_services => $delete_services,
        create_services => $create_services,
        update_services => $update_services,
    };
}

sub add_info_message {

    my $message = shift;
    $info_msg .= $message."<BR>"; 
}

sub add_error_message {
   
    my $message = shift;
    $error_msg .= $message."<BR>";
}

sub validate_item_action {
  
    my ($flags,$action) = @_;
    my $allowed = 0;

    if ( $action eq 'zone') {
       $allowed = 1 if $flags->{allow_zone_management};  
    } elsif ( $action eq 'forwarding') {
       $allowed = 1 if $flags->{allow_url_forwarding} || 
                       $flags->{allow_templates};
    } 
   
    return $allowed;
}
