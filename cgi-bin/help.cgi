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
BEGIN {
      $path_to_config = '/home/westcoas/opensrs-client-3.0.0/etc';	
      do "$path_to_config/OpenSRS.conf";
}

use lib $PATH_LIB;
use strict;
use CGI qw();
use IO::File;
use Core::Exception;
use OpenSRS::Help qw/HelpPages/;
use OpenSRS::Util::Error;
use OpenSRS::Util::Logger '$Log';# =>"$PATH_LOG/help.log";

my $path_templates = "$PATH_TEMPLATES/help";

my $q = new CGI;

try {
    if ($q->param('tld')){
	$path_templates .= '/' .$q->param('tld');
    }
    my $topic = $q->param('topic');
    unless (HelpPages->{$topic}){
	throw 'dev','Invalid topic \'%s\'',$topic;
    }
    my $fh = IO::File->new($path_templates."/".HelpPages->{$topic},O_RDONLY);
    unless ($fh){
	throw 'dev','Can\'t find help file for topic \'%s\'',$topic;
    }
    print $q->header;
    my @content = <$fh>;
    undef $fh;
    print @content;

} catch {
    dev => sub {
	my $E = shift;
	$Log->error("dev %s",$E->dump);
	print $q->header;
	error_output($E->info);
    },
    _other => sub {
	my $E = shift;
	$Log->error("other %s",$E->dump);
	print $q->header;
	error_output($E->info);
    },
};

exit;
1;

