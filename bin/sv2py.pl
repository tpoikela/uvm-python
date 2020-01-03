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
use File::Basename;
use File::Spec;

my $DEBUG = 0;

my %opt;
GetOptions(
    "file|f=s" => \$opt{f},
    "all"      => \$opt{all},
    "d|debug"  => \$DEBUG,
);

my @suffixlist = ('.py');

my @files = ();

if (defined $opt{f} and -e $opt{f}) {
    process_file($opt{f});
}
elsif (defined $opt{all}) {
    @files = glob("*.sv");
    push(@files, glob("*.svh"));
}
else {
    @files = @ARGV;
}

my $pkg_map = build_pkg_map();


# Finally process the input files here
for my $file (@files) {
    my $res = process_file($file);
    if ($file =~ /(\w+)\.svh?/) {
        my $py_file = "$1.py";
        open(my $OFILE, ">", $py_file) or die $!;
        print $OFILE $res;
        close($OFILE);
        print "Created new file $py_file\n";
    }
}

#---------------------------------------------------------------------------
# HELPERS
#---------------------------------------------------------------------------

sub process_file {
    my ($fname) = @_;
    open(my $IFILE, "<", $fname) or die $!;
    my $lineno = 0;
    my $skipped_lines = 0;

    my @outfile = ();
    my $ind = 0;
    my $def_conn_phase = "def connect_phase(self, phase):";
    my $def_build_phase = "def build_phase(self, phase):";

    my $import_line = -1;
    my @imports = ();

    while (<$IFILE>) {
        my $line = $_;
        my $ws = " " x (4 * $ind);
        ++$lineno;

        if ($import_line == -1 && $line =~ /^\s*import /) {
            $import_line = $lineno;
        }

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
        $line =~ s/(\W)'h([a-fA-F0-9]+)/$1 0x$2/g;
        $line =~ s/(\W)'b([01]+)/$1 0b$2/g;

        # Imports are added here
        if ($line =~ /`uvm_(component|object)_utils/) {
            push(@imports, "#from uvm.macros import *\n");
        }
        elsif ($line =~ /extends uvm_(\w+)/) {
            my $imp_name = "uvm.base.uvm_$1";
            if (exists $pkg_map->{"uvm_$1"}) {
                $imp_name = $pkg_map->{"uvm_$1"};
            }
            push(@imports, "#from $imp_name\n");
        }


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

    # Add imports to the import line
    splice(@outfile, $import_line, 0, @imports);

    if (defined $opt{f}) {
        for my $line (@outfile) {
            print $line;
        }
    }

    close($IFILE);
    return wantarray ? @outfile : join('', @outfile);
}


sub build_pkg_map {
    my @py_sources = glob("$ENV{UVM_PYTHON}/uvm/**/*.py");
    my $pkg_map = {};
    foreach my $f (@py_sources) {
        my ($name,$path,$suffix) = fileparse($f, @suffixlist);
        my @path = File::Spec->splitdir($path);
        my $pkg_path = "";
        my $found = 0;
        for my $p (@path) {
            print "|$p|\n" if $DEBUG;
            if ($found == 1) {
                $pkg_path .= "$p." if length($p) > 0;
            }
            if ($p =~ /uvm-python/) {
                $found = 1;
            }
            else {
                print "$p not matcing yet\n" if $DEBUG;
            }
        }
        $pkg_path =~ s/\.$//g;  # Trim trailing dot
        print "\npkg map: $name -> $pkg_path\n" if $DEBUG;
        $pkg_map->{$name} = "$pkg_path.$name";
    }
    return $pkg_map;
}
