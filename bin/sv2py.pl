#!/usr/bin/env perl 
#===============================================================================
#
#         FILE: sv2py.pl
#
#        USAGE: ./sv2py.pl  
#
#  DESCRIPTION: Convert some SV structs into Python. Does not do full
#               conversion. 
#
#      OPTIONS: ---
# REQUIREMENTS: ---
#         BUGS: ---
#        NOTES: ---
#       AUTHOR: Tuomas Poikela (tpoikela), tuomas.sakari.poikela@gmail.com
# ORGANIZATION: ---
#      VERSION: 1.0
#      CREATED: 01/01/2020 05:41:28 PM
#     REVISION: ---
#===============================================================================

use strict;
use warnings;
use utf8;

use Getopt::Long;

my %opt;
GetOptions(
    "file|f=s" => \$opt{f}
);

open(my $IFILE, "<", $opt{f}) or die $!;

my @outfile = ();

my $ind = 0;

my $def_conn_phase = "def connect_phase(self, phase):";
my $def_build_phase = "def build_phase(self, phase):";

while (<$IFILE>) {
    my $line = $_;
    my $ws = " " x (4 * $ind);

    if ($line =~ /^(.*)All rights reserved worldwide/i) {
        my $cline = "#$1Copyright 2019-2020 Tuomas Poikela (tpoikela)\n";
        push(@outfile, $cline);
    }

    if ($line =~ /^\s*(virtual\s+)?task /) {
        push(@outfile, "$ws#\@cocotb.coroutine\n");
    }
    
    $line =~ s/;$//g;  # Remove trailing semicolon
    $line =~ s/\s*==\s*null/ is None/g;
    $line =~ s/\s*!=\s*null/ is not None/g;
    $line =~ s/\bnull\b/None/g;
    $line =~ s/\bthis\b/self/g;
    $line =~ s/\) begin\b/):/g;
    $line =~ s/\belse\s+if\b/elif/g;
    $line =~ s/function new\(string name/def __init__(self, name/g;
    $line =~ s/::type_id::create/.type_id.create/g;
    $line =~ s/super\.new\(/super().__init__(/g;


    # Replace standard UVM functions
    $line =~ s/virtual function void build\(\)/$def_build_phase/g;
    $line =~ s/virtual function void connect\(\)/$def_build_phase/g;
    $line =~ s/virtual function void connect_phase\(uvm_phase phase\)/$def_conn_phase/g;
    $line =~ s/virtual function void build_phase\(uvm_phase phase\)/$def_build_phase/g;
    $line =~ s/class (\w+) extends (\w+)/class $1($2):/g;

    # SystemVerilog functions
    $line =~ s/\$(urandom|sformatf|cast)/sv.$1/g;
    

    $line =~ s/uvm_config_db#\(.*\)::(set|get)/UVMConfigDb.$1/g;
    $line =~ s/uvm_resource_db#\(.*\)::(set|get)/UVMResourceDb.$1/g;

    push(@outfile, "$ws#$line");

    if ($line =~ /^class /) {++$ind;}
    elsif ($line =~ /^endclass/) {--$ind;}
}

for my $line (@outfile) {
    print $line;
}
