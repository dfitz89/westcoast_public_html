#!/usr/local/bin/perl

#       .Copyright (C)  1999-2000 TUCOWS.com Inc.
#       .Created:       01/13/2000
#       .Contactid:     <admin@opensrs.org>
#       .Url:           http://www.opensrs.org
#       .Originally Developed by:
#                       VPOP Technologies, Inc. for Tucows/OpenSRS
#       .Authors:       Joe McDonald, Tom McDonald, Matt Reimer, Brad Hilton,
#                       Daniel Manley, Mark
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

use strict;
use vars qw($shell $cipher @modules $optional);
( $shell, $cipher ) = ();

# pull in conf file with defined values
# XXX NOTE XXX Update this configuration file
BEGIN {
    if ($ENV{OSRS_CLIENT_ETC}){
	do "$ENV{OSRS_CLIENT_ETC}/OpenSRS.conf";
    } else {
	do "/home/westcoas/opensrs-client-3.0.0/etc/OpenSRS.conf";
    }
}

# PATH_LIB = "/usr/local/opensrs-client-3.0.0/OpenSRS.conf";
my $PATH_LIB = "/usr/local/opensrs-client-3.0.0/OpenSRS.conf";
use lib $PATH_LIB;
use Config;
use IO::Socket;

# global defines
$shell = 0;
$cipher = "";
$optional = 0;

# list of modules to check for existence of.  No need to check for standard
# modules, or ones that are included in the client code distribution.
my @CBC_modules = qw(
	Digest::MD5
	Unicode::String
	Storable
	Data::Dumper
	HTML::Template
	XML::Parser
);
if ($] >= 5.008) {
    push @CBC_modules => "Crypt::CBC";
} else {
    push @CBC_modules => "CBC";
}


my @HTTPS_modules = qw(
        Digest::MD5
        Unicode::String
        Storable
        Data::Dumper
        HTML::Template
        XML::Parser
        LWP::UserAgent
        LWP::Protocol::https
        HTTP::Request::Common
);

my @LibIDN_modules = qw(Net::LibIDN);

my @Date_modules = qw(Date::Calc);
# common
start_up();
check_settings();


# get connection type
my $connection_type = $OPENSRS{connection_type};
my $oposite_type = $OPENSRS{connection_type} eq 'HTTPS' ? 'CBC' : 'HTTPS';

@modules = $connection_type eq 'HTTPS' ? @HTTPS_modules : @CBC_modules;
check_modules($connection_type);
check_osrs_modules();
$connection_type eq 'HTTPS' ? check_login_https() : check_login();
shut_down();

start_optional();

@modules = $oposite_type eq 'HTTPS' ? @HTTPS_modules : @CBC_modules;
check_modules($oposite_type);
check_osrs_modules();
$oposite_type eq 'HTTPS' ? check_login_https() : check_login();

@modules = @LibIDN_modules;
start_idn();
check_modules('IDN');
check_osrs_idn();

@modules = @Date_modules;
start_date();
check_modules('Date::Calc');

shut_down();

exit;

sub start_up {

    if (not $ENV{SCRIPT_NAME}) {
	$shell = 1;
	print "\n_________OpenSRS Client Debugger__________\n\n";
    } else {
	print "Content-type:  text/html\n\n";
	print <<EOF;
<head>
<meta http-equiv="Content-type" content="text/html; charset=UTF-8">
</head>
<body bgcolor=white>
<center>
<font size="+3" face="Arial, Helvetica, sans-serif"><b>OpenSRS Client Debugger</b></font>

<br><br>
<table bgcolor="#ffffff" border="0" cellpadding="5" cellspacing="1" width="80%">
EOF
        print_th('Client Software Configuration');
    }

    # print error to the page
    select (STDOUT); $| = 1;
    open (STDERR, ">&STDOUT") or die "Can't dump stdout: $!\n";
    select (STDERR); $| = 1;
    select (STDOUT);

}

sub shut_down {

    if (not $shell) {
	print <<EOF;
</table>
</body>
</html>
EOF
    }
    
}

sub start_optional {
   $optional = 1;

   my $msg1 = "This test will check the requirements for the connection type other than the one currently selected.";
   my $msg2 = "It is provided to indicate your readiness to switch between different connection types.";
   my $msg3 = "The failure at any point of this test does NOT impact the operation of the current configuration.";

   if (not $shell) {
       print <<EOF;
</table>
<br>
<table bgcolor="#ffffff" border="0" cellpadding="5" cellspacing="1" width="80%">

<tr bgcolor="#COD1DD">
 <td colspan="2">
   <b>$msg1<br>$msg2<br>$msg3</b>
 </td>
</tr>
EOF
   } else {
      print("\n".("-" x 80)."\n".$msg1."\n".$msg2."\n".$msg3."\n".("-" x 80)."\n"); 
   }
}

sub start_idn {
   
   my $msg1 = "Following tests will check the requirements for the IDN (Internationalized Domain Name) conversion.";
   my $msg2 = "Tests will check local conversion support (using Net::LibIDN), and OpenSRS IDN conversion server connection and operation.";
   my $msg3 = "If the conversion is supported locally, any failures reported for OpenSRS conversion server will not impact your operations.";
   my $msg4 = "If the conversion is supported using OpenSRS conversion server, any failure reported for local support (Net::LibIDN) will not impact your operations.";

   if (not $shell) {
       print <<EOF;
</table>
<br>
<table bgcolor="#ffffff" border="0" cellpadding="5" cellspacing="1" width="80%">

<tr bgcolor="#COD1DD">
 <td colspan="2">
   <b>$msg1<br>$msg2<br>$msg3<br>$msg4</b>
 </td>
</tr>
EOF
   } else {
      print("\n".("-" x 80)."\n".$msg1."\n".$msg2."\n".$msg3."\n".("-" x 80)."\n"); 
   }
}

sub start_date {

 
   my $msg1 = "Following tests will check the requirements for the Date Calculation.";
   my $msg2 = "Tests will check date calculation support (using Date::Calc).";

 
   if (not $shell) {
       print <<EOF;
</table>
<br>
<table bgcolor="#ffffff" border="0" cellpadding="5" cellspacing="1" width="80%">

 
<tr bgcolor="#COD1DD">
 <td colspan="2">
   <b>$msg1<br>$msg2</b>
 </td>
</tr>
EOF
   } else {
      print("\n".("-" x 80)."\n".$msg1."\n".$msg2."\n".("-" x 80)."\n");
  }
}
sub check_settings {

    my $uname;

    if ( not $shell) {
        print_message("Verify Install URL", "http://$ENV{HTTP_HOST}$ENV{REQUEST_URI}");
        print_message("OpenSRS Client IP Address", $ENV{SERVER_ADDR});
    }

    print_message("OpenSRS version", $OpenSRS::VERSION || "Unknown" );
    print_message("Perl version", $]);

    # attempt to display the OS type (requires uname to be in your path)
    foreach my $path ( '/bin', '/usr/bin', (split /:/, $ENV{PATH})) {
   		if (-x "$path/uname") {
	    	chomp($uname = `$path/uname -a`);
	    	print_message("Operating System", $uname);
	    	last;
		}
    }

    if (defined $Config{osname}) {
		print_message("Perl compiled for", "$Config{osname} ($Config{archname})");
    }

    if ($OPENSRS{connection_type} =~ /^(CBC|HTTPS)$/) {
        print_message("Connection Type", $OPENSRS{connection_type});
    } else {
        print_error("Connection Type", "ERROR: Unknown connection type $OPENSRS{connection_type}.  Please check the value of \$OPENSRS{connection_type} in your configuration file");
        shut_down();
        exit;
    }

    print_message("Server Hostname", $OPENSRS{REMOTE_HOST});
    print_message("Server Port", $OPENSRS{REMOTE_PORT});
    if ( $OPENSRS{connection_type} eq 'HTTPS' &&
         not $OPENSRS{REMOTE_HTTPS_PORT}) 
    {
        print_error("HTTPS Port", "ERROR: HTTPS port must be specified for the current configuration [HTTPS]");
        shut_down();
        exit;
    } else {
        print_message("HTTPS Port", $OPENSRS{REMOTE_HTTPS_PORT});
    }

    print_message("Reseller Username", $OPENSRS{username});
    print_message("Private Key Length", length $OPENSRS{private_key});
    
    print_th("Encryption [$OPENSRS{connection_type}]");

    if ( $OPENSRS{connection_type} eq 'CBC') {
        if ($OPENSRS{crypt_type} =~ /^(DES|Blowfish|Blowfish_PP)$/) {
            print_message("Encryption Method", $OPENSRS{crypt_type});
        } else {
            print_error("Encryption Method", "ERROR: Unknown crypt type $OPENSRS{crypt_type}.  Please check the value of \$OPENSRS{crypt_type} in your configuration file");
            shut_down();
            exit;
        }
    } else {
        print_message("Encryption Method","SSL");
    }

    if ( $OPENSRS{connection_type} eq 'CBC') {
        test_for_module("Crypt::$OPENSRS{crypt_type}");
    }

}

sub check_modules {

    my $ctype = shift;
    my $th = "Software Requirement Tests [$ctype]";
    $th .= " (Local IDN conversion support)" if $ctype eq 'IDN';
    
    print_th($th);

    test_for_module($_) foreach @modules;

}

sub test_for_module {
	my $module = shift;
	my $test = "Checking for this $module";
	
	eval "require $module";
	if ( $@ ) {
		print_error($test, "ERROR: $module not found: $@");
		unless ($optional){
		    shut_down();
		    exit;
		}
		print_message($test, "Failed");
		return;
	}
	my $version = eval "\$${module}::VERSION";
	print_message($test, "OK ".($version ? "(version $version)" : ""));
}

sub check_osrs_idn {

    print_th('OpenSRS IDN Conversion Server Test');

    my $ua = LWP::UserAgent->new;
    my $test = "Connecting to conversion server";
    my $test2 = "Converting IDN [Punycode to Native]";    
    my $test3 = "Converting IDN [Native to Punycode]";    
    my $name = 'xn--6oq304hzhk0hl.com';
    my $encoding = $OPENSRS{IDN_ENCODING_TYPE};
    my $http_request = HTTP::Request::Common::GET (
	'http://'.$OPENSRS{REMOTE_IDN_HOST}.':'.$OPENSRS{REMOTE_IDN_PORT}."?to=$encoding&name=$name"
    );
    my $response = $ua->request($http_request);
    my $response2 = undef;
    
    if ( defined $response and $response->is_success ) {
	print_message($test, "OK"); 
	$response2 = parse_http_response($response);
	if ( defined $response2 and $response2->{is_success} ) {
	    print_message($test2, "OK - FROM: $response2->{punycode} TO: $response2->{native}");
	} else {
	    #can connect but conversion failed
	    print_error($test2, "Conversion failed: $response2->{response_text}");
	}
    } else {
	print_error($test, "ERROR: Unable to login to conversion server");
        return;
    }
    
    $name = $response2->{native};
    $http_request = HTTP::Request::Common::GET (
	'http://'.$OPENSRS{REMOTE_IDN_HOST}.':'.$OPENSRS{REMOTE_IDN_PORT}."?from=$encoding&name=$name"
    );
    $response = $ua->request($http_request);
    my $response3 = parse_http_response($response);
    if ( defined $response3 and $response3->{is_success} ) {
	print_message($test3, "OK - FROM: $response3->{native} TO: $response3->{punycode}");
    } else {
	print_error($test3, "Conversion failed: $response3->{response_text}");
    }
}

sub parse_http_response {
    my $http_response = shift;
    my %response;
    
    foreach ( split "\015\012", $http_response->content ) {
	$response{$1} = $2 if $_ =~ /(.*)=(.*)/;
    }   

    return \%response; 
}

sub check_osrs_modules {

    require OpenSRS::XML_Client;
    require OpenSRS::TPP_Client;
    
    print_th('OpenSRS Client Modules');
                                                                                                                                                                                                     
    print_message("XML Client Version", $OpenSRS::XML_Client::VERSION);
    print_message("TPP Client Version", $OpenSRS::TPP_Client::VERSION);
}

sub check_login_https {
   
    require OPS;
    require HTTP::Request::Common;
    require LWP::UserAgent;
    require LWP::Protocol::https;
    require Digest::MD5;

    {
	my $net_ssl_ok = 1;
	print_th("Checking for Net::SSL");
	eval { require Net::SSL; };
	if ($@) {
	    $net_ssl_ok = 0;
	    print_message("Net::SSL",$@);
	}
	my $io_socket_ok = 1;
	print_th("Checking for IO::Socket::SSL");
	eval { require IO::Socket::SSL; };
	if ($@) {
	    $io_socket_ok = 0;
	    print_message("IO::Socket::SSL",$@);
	}
	unless ($io_socket_ok || $net_ssl_ok){
	   print_error("HTTPS","Some modules missing from perl installation test may fail");
	}

	
    }

    print_th('HTTPS Authentication Test');

    my $test = "Logging in to OpenSRS server";

    my $answer = auth_https();

    if ( not $answer ) {
        print_error($test, "ERROR: Unable to login to server");
    } else {
        print_message($test, "OK");
    }
}

sub auth_https {

    my $OPS = new OPS();
    my $ua = LWP::UserAgent->new;
    
    my $request = {
        protocol => 'XCP',
        action => 'lookup',
        object => 'domain',
        attributes => {
            domain => 'tucows.com',
        }
    };

    my $xml = $OPS->encode($request)."\n";
    my $signature = Digest::MD5::md5_hex(Digest::MD5::md5_hex($xml,$OPENSRS{private_key}),$OPENSRS{private_key});
    my $https_request = HTTP::Request::Common::POST (
              'https://'.$OPENSRS{REMOTE_HOST}.':'.$OPENSRS{REMOTE_HTTPS_PORT},
              'Content-Type' => 'text/xml',
              'X-Username'     => $OPENSRS{username},
              'X-Signature'    => $signature,
              'Keep-Alive'  =>'off',
              'Content-Length' => length($xml),
              'Content'      => $xml
       );
                                                                                                                                                                                                     
    my $response = $ua->request($https_request);
    
    if (defined $response and $response->is_success){
	my $response2 = $OPS->decode($response->{_content});
	if ( defined $response2 and $response2->{is_success}) {
	    return 1;
	} else {
	    #can connect but key is invalid or Lookup failed
	    print_error("auth_https","can connect but key is invalid or Lookup failed");
	    return 0;
	}
    } else {
       return 0;
    }

}

sub check_login {

    # keep the following as require statements, rather than use, so we
    # can check for any external modules that they may require.  No
    # point having verify_install bomb out for something that's missing,
    # when it's supposed to tell you what's missing. :)  They should also
    # stay here, rather than at the top of the code for the same reason.

    require OPS;

    my ($fh);

    print_th('CBC Authentication Test');

    my $test = "Logging in to OpenSRS server";

    # make or get the socket filehandle
    if (not $fh = init_socket()) {
	print_error($test, "ERROR: Unable to establish socket!");
	return;
    }
    my $answer = authenticate($fh);

    if (not $answer) {
	print_error($test, "ERROR: Unable to login to server.  Make sure you have properly defined the \$USERNAME and \$PRIVATE_KEY values in your configuration file");
    } elsif ($answer != 1) {
	print_error($test, "ERROR: Unable to login to server: $answer");
	close_socket($fh);
    } else {
	print_message($test, "OK");
	close_socket($fh);
    }

}

sub authenticate {
    
    my ($answer,$prompt);
    my ($challenge, $session_key);
    
    my $fh = shift;
    my $OPS = new OPS();

    if (not $OPENSRS{username} or not $OPENSRS{private_key}) {
	return "400\tMissing username or crypt key";
    }
    
    $prompt = read_data( $fh, $OPS );

    if ( $prompt->{response_code} == 555 ) {
        # the ip address from which we are connecting is not accepted
        return ( $prompt->{response_text} );
    } elsif ( $prompt->{attributes}->{sender} !~ /OpenSRS\sSERVER/ ||
    	 $prompt->{attributes}->{version} !~ /^XML/ ) {
	return ( "401\tUnrecognized Peer" );
    }

    # first response is server version
    send_data( $fh, $OPS, {
    	    action => "check",
	    object => "version",
	    attributes => {
		    sender => "OpenSRS CLIENT",
		    version => $OpenSRS::XML_Client::VERSION,
		    state => "ready",
		    }
    	    } );

    my $crypt = lc $OPENSRS{crypt_type};
    if ($crypt eq 'blowfish_pp') { $crypt = 'blowfish' }

    send_data( $fh, $OPS, {
    	    action => "authenticate",
	    object => "user",
	    attributes => {
	    	    crypt_type => $crypt,
		    username => $OPENSRS{username},
		    password => $OPENSRS{username},
	    	    }
    	    } );

    # Encrypt the challenge bytes with our password to generate
    # the session key.

    # Respond to the challenge with the MD5 checksum of the challenge.
    $challenge = read_data( $fh, $OPS, no_xml => 1 );

    if ($Crypt::CBC::VERSION >= 2.17){
	$cipher = new Crypt::CBC(
	    -key => pack('H*', $OPENSRS{private_key}), 
	    -cipher => $OPENSRS{crypt_type},
	    -header => 'randomiv'
	);
    } else {
	$cipher = new Crypt::CBC(pack('H*', $OPENSRS{private_key}), $OPENSRS{crypt_type});
    }
    
    send_data( $fh, $OPS, Digest::MD5::md5( $challenge ), no_xml => 1);

    # Read the server's response to our login attempt.
    # This is in XML
    $answer = read_data( $fh, $OPS );

    if ($answer->{response_code} =~ /^2/) {
	return 1;
    } elsif ( $answer->{response_code} == 400 ) {
	return $answer->{response_text};    
    } else {
	return "Authentication failed";
    }
}

sub init_socket {
    
    my ($REMOTE_HOST,$REMOTE_PORT,$fh,$connect_type);

    $REMOTE_HOST = $OPENSRS{REMOTE_HOST};
    $REMOTE_PORT = $OPENSRS{REMOTE_PORT};

    # create a socket
    $fh = IO::Socket::INET->new(
                Proto 	        => "tcp",
                PeerAddr        => $REMOTE_HOST,
                PeerPort        => $REMOTE_PORT,
                );
    
    if ( not defined $fh )
    {
    	return 0;
    }

    select($fh); $| = 1;
    select(STDOUT);
    
    return $fh;
    
}

sub close_socket {
    
    my ($fh) = @_;
    close($fh);
    $cipher = undef;
}

sub read_data {
    my $buf;
    my $fh = shift;
    my $OPS = shift;
    my %args = @_;

    # Read the length of this input.
    $buf = $OPS->read_data( $fh );
    
    $buf = ($cipher) ? $cipher->decrypt($buf) : $buf;
    if ( not $args{no_xml} ) {
    	$buf = $OPS->decode( $buf );
    }

    return $buf;
}

# Sends request to the server.
# XXX Need error checking?
sub send_data {

    my $fh = shift;
    my $OPS = shift;
    my $message = shift; # hash ref or binary data (for challenge)
    my %args = @_;  # other flags
    my $data_to_send;

    if ( not $args{no_xml} ) {
	$message->{protocol} = "XCP";
	$data_to_send = $OPS->encode( $message );
    } else {
    	# no XML encoding
    	$data_to_send = $message;
    }
    $data_to_send = $cipher->encrypt($data_to_send) if $cipher;

    return $OPS->write_data( $fh, $data_to_send );
}

sub print_message {

    my ($test, $response) = @_;

    if ($shell) {
	printf("%-30s: %s\n",$test, $response);
    } else {
	print <<EOF;
<tr bgcolor="#CEE1EF">
<td align="right" width="%30"><b><font face="Arial, Helvetica, sans-serif">$test</font></b></td>
<td><font face="Arial, Helvetica, sans-serif">$response</font></td>
</tr>
EOF
    }
}

sub print_error {

    my ($test, $response) = @_;

    if ($shell) {
	printf("%-30s: %s\n",$test, $response);
    } else {
	print <<EOF;
<tr bgcolor="#CEE1EF">
<td align="right" width="%30"><b><font face="Arial, Helvetica, sans-serif">$test</font></b></td>
<td><font color="red" face="Arial, Helvetica, sans-serif">$response</font></td>
</tr>
EOF
    }
}

sub print_th {
    
    my $header = shift;
   
    if (not $shell) {
                print <<EOF;
<tr>
<th colspan=2 bgcolor="#C0D1DD"><font face="Arial, Helvetica, sans-serif">$header</font></th>
</tr>
EOF
    } else {
	print "==========================================\n";
	print $header,"\n\n";
    }
}
