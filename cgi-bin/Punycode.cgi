#!/usr/local/bin/perl

#       .Copyright (C)  2004 Tucows Inc.
#       .Created:       04/02/2004
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Authors:       Vlad Jebelev, Tom Lovasic, Steve Knipe, Vedran Vego
#
#
#       This program is free software; you can redistribute it and/or
#       modify it under the terms of the GNU Lesser General Public
#       License as published by the Free Software Foundation; either
#       version 2.1 of the License, or (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#       Lesser General Public License for more details.
#
#       You should have received a copy of the GNU Lesser General Public
#       License along with this program; if not, write to the Free Software
#       Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA



use vars qw($cgi $path_templates %in $flag_header_sent %strings);

BEGIN {

    $path_to_config = "/home/westcoas/opensrs-client-3.0.0/etc";
    do "$path_to_config/OpenSRS.conf";
}

use warnings;
use strict;

use lib $PATH_LIB;
use CGI ':cgi-lib';
use HTML::Template;
use RACE;
use OpenSRS::Util::Common;
use OpenSRS::Language qw/native_to_puny puny_to_native/;
RACE::Initialise(%RACESETTINGS);

$cgi = $ENV{SCRIPT_NAME};
$path_templates = "$PATH_TEMPLATES/PUNYCODE";
$flag_header_sent = 0;
%strings = ();

%in = ();
ReadParse(\%in);
foreach (keys %in) {
    $in{$_} =~ s/(^\s+)|(\s+$)//g;
}

start_up();

my $type = $in{type};
my $text = $in{input};

if ( $text ) {
    if ($type eq 'NATIVE') {

	$strings{native} = $text;

	eval { $strings{race} = native_to_race($text)};
	if ( $@ ) { $strings{race} = undef; $strings{error_race} = $@; }

	eval { $strings{punycode} = native_to_puny($text, \%OPENSRS)};
	if ( $@ ) { $strings{punycode} = undef; $strings{error_punycode} = $@; }

    } elsif ($type eq 'RACE') {

	eval { $strings{native} = race_to_native($text)};
	if ( $@ ) { $strings{native} = undef; $strings{error_native} = $@; }
	
	$strings{race} = $text;

	eval { my $native = race_to_native($text);
	       $strings{punycode} = native_to_puny($native, \%OPENSRS)};
	if ( $@ ) { $strings{punycode} = undef; $strings{error_punycode} = $@; }

    } elsif ($type eq 'PUNYCODE') {

	eval { $strings{native} = puny_to_native($text, \%OPENSRS)};
	if ( $@ ) { $strings{native} = undef; $strings{error_native} = $@; }

	eval { my $native = puny_to_native($text, \%OPENSRS);
	       $strings{race} = native_to_race($native)};
	if ( $@ ) { $strings{race} = undef; $strings{error_race} = $@; }

	$strings{punycode} = $text;
    }
}

main_menu();
exit;

sub native_to_race {
    my ( $str ) = @_;

    my $conv = RACE::DoRACE( Domain => $str, EncodingType => $OPENSRS{IDN_ENCODING_TYPE});

    if ($conv->{Error}){
	die $conv->{Error}."\n";
    }

    return $conv->{ConvertedDomain};
}

sub race_to_native {
    my ( $str ) = @_;
    
    my $conv = RACE::UndoRACE( Domain => $str, EncodingType => $OPENSRS{IDN_ENCODING_TYPE});

    if ($conv->{Error}){
	die $conv->{Error}."\n";
    }

    return $conv->{OriginalDomain};
}

sub main_menu {
    my (%HTML);
    
    print_form(template => "$path_templates/base.html",
	       data => {
		%in,
		%strings,
		encoding => uc $OPENSRS{IDN_ENCODING_TYPE},
	        show_results => (scalar(keys %strings) > 0 ? 1 : 0),
		show_race => ($in{type} ne 'RACE' && exists $strings{race}),
		show_native => ($in{type} ne 'NATIVE' && exists $strings{native}),
		show_punycode => ($in{type} ne 'PUNYCODE' && exists $strings{punycode}),
	       });
}

sub print_form {
    my %args = @_;
    
    $args{title} = $args{title} || 'IDN Converter';
    
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
    );

    print_header();
    print $template->output;
}

# print html header
sub print_header {
    my %cookies = @_;

    return if $flag_header_sent;
    
    print "Content-type: text/html\r\n";
    foreach my $key (keys %cookies) {
	printf "Set-Cookie: %s=%s; PATH=;\r\n", $key, $cookies{$key};
    }
    print "\r\n";
    
    $flag_header_sent = 1;
}

sub start_up {
    OpenSRS::Util::Common::initialize(
	path_templates => $PATH_TEMPLATES,
	mail_settings => \%MAIL_SETTINGS
    );
}

