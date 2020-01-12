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
    "author=s" => \$opt{author},
    "p|print"  => \$opt{print},
    "f|force"  => \$opt{force},
);

my $AUTHOR = $opt{author} || "Tuomas Poikela (tpoikela)";

my $re_qual = qr/(protected|local)/; # $1
my $re_type = qr/(\w+(#\(\w+\))?)/;  # $2, $3, $4
my $re_packed = qr/(\[.*\])?/;       # $5
my $re_name = qr/(\w+)/;             # $6
my $re_unpacked = qr/((\[.*\])+)/;   # $7, $8 (full)
my $re_init_var = qr/(=[^;]+)/;      # $9
my $re_var = qr/(rand)?$re_qual?\s*$re_type\s*$re_packed\s*$re_name\s*$re_unpacked?$re_init_var?\s*;\s*$/;

my $conf_db_re = qr/uvm_config_db#\(.*\)::(set|get)/;
my $res_db_re = qr/uvm_resource_db#\(.*\)::(set|get)/;

my $GLOBAL = 1 << 0;
my $IN_CLASS = 1 << 1;
my $IN_NEW = 1 << 2;
my $IN_TASK = 1 << 3;
my $IN_FUNC = 1 << 4;

my $st = $GLOBAL;

my @suffixlist = ('.py', '.sv', '.svh');

my @files = ();
my $pkg_map = build_pkg_map();


if (defined $opt{f} and -e $opt{f}) {
    #process_file($opt{f});
    push(@files, $opt{f});
}
elsif (defined $opt{all}) {
    @files = glob("*.sv");
    push(@files, glob("*.svh"));
}
else {
    @files = @ARGV;
}


# Finally process the input files here
for my $file (@files) {
    my $res = process_file($file);
    my $is_sv = $file =~ /(\w+)\.svh?/;

    # Write only .svh files to output
    if ($is_sv) {
        my $py_file = "$1.py";
        if (is_safe_to_write($py_file)) {
            open(my $OFILE, ">", $py_file) or die $!;
            print $OFILE $res;
            close($OFILE);
            print "Created new file $py_file\n";
        }
    }

    if (defined $opt{print}) {
        print $res;
    }
    elsif (not $is_sv) {
        print STDERR "Python files don't produce any output. Specify -p|-print\n";
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

    my ($name,$path,$suffix) = fileparse($fname, @suffixlist);
    my $is_py = $suffix eq '.py' ? 1 : 0;

    if (length($suffix) == 0) {
        print STDERR "Parsing file with without suffix not supported. File: $fname\n";
    }

    my @outfile = ();
    my $ind = 0;
    my $def_conn_phase = "def connect_phase(self, phase):";
    my $def_build_phase = "def build_phase(self, phase):";

    my $new_endfunction = -1;
    my $import_line = -1;
    my $include_line = -1;
    my $ifndef_line = -1;

    my @imports = ();

    my @found_vars = ();
    my $has_author = $is_py;  # Do not re-insert to py files

    while (<$IFILE>) {
        my $line = $_;
        my $ws = " " x (4 * $ind);
        ++$lineno;
        my $add_line = 1;  # If set to 0, skip adding this line to file

        if ($is_py and $line !~ /^\s*#/) {
            print "Skipping line $lineno: $line.\n";
            push(@outfile, $line);
            next;
        }

        # Skip commented
        if ($is_py == 0 && $line =~ m{^\s*//} && $has_author) {
            push(@outfile, "$ws#$line");
            next;
        }

        # Look for line in which imports start
        if ($import_line == -1 && $line =~ /^\s*import /) {
            $import_line = $lineno;
        }
        elsif ($include_line == -1 && $line =~ /^\s*`include/) {
            $include_line = $lineno;
        }
        elsif ($ifndef_line == -1 && $line =~ /^\s*`ifndef/) {
            $ifndef_line = $lineno;
        }

        if ($line =~ /^(.*)All rights reserved worldwide/i) {
            my $cline = "#$1Copyright 2019-2020 $AUTHOR\n";
            my $has_author = 1;
            push(@outfile, $cline);
        }

        # Check for various tasks and functions
        if ($line =~ /^\s*(virtual\s+)?(protected\s+)?task\s+(\w+)/) {
            my $task_name = $1;
            $st = $st | $IN_TASK;
            push(@outfile, "$ws#\@cocotb.coroutine\n");
            add_import(\@imports, "import cocotb\n");
        }
        elsif ($line =~ /^\s*endtask/) {
            $st = ~$IN_TASK & $st;
        }
        elsif ($line =~ /^\s*(virtual\s+)?(protected\s+)?function\s+(\w+)/) {
            my $func_name = $1;
            $st = $st | $IN_FUNC;
        }
        elsif ($line =~ /^\s*endfunction/) {
            $st = ~$IN_FUNC & $st;
        }

        if ($st == $IN_CLASS) {
            if ($line !~ m{^\s*//} && $line =~ $re_var) {
                #=~ /^\s*(local|protected(\s+))?(\w+(#\(\w+\))?)\s+(\w+)\s*;/) {
                my $value = "None";
                my $var_type = $3;
                my $var_name = $6;
                my $unpacked = $8;
                my $var_init = $9;
                print("$fname,$lineno var matches: $var_name, init: $var_init\n");
                if ($var_type =~ /\bint(eger)?\b/ ) {$value = 0;}
                if ($var_type =~ /\bstring\b/ ) {$value = "";}
                if (defined $var_init) {
                    $value = $var_init;
                    $value =~ s/=//;
                }
                my $self_var = "${ws}#    self.$var_name = $value  # $var_type\n";
                push(@found_vars, $self_var);
            }
        }
        if ($line =~ /function\s+new\s*\(/) {
            $st = $st | $IN_NEW;
        }
        elsif (($st & $IN_NEW) && $line =~ /endfunction/) {
            $new_endfunction = $lineno;
            $st = $st & ~$IN_NEW;
        }

        $line =~ s/;$//g;  # Remove trailing semicolon
        $line =~ s/\s*==\s*null/ is None/g;
        $line =~ s/\s*!=\s*null/ is not None/g;
        $line =~ s/\bnull\b/None/g;
        $line =~ s/\bthis\b/self/g;
        $line =~ s/\) begin\b/):/g;
        $line =~ s/\belse\s+if\b/elif/g;
        $line =~ s/function new\s*\(string name/def __init__(self, name/g;
        $line =~ s/::type_id::create/.type_id.create/g;
        $line =~ s/super\.new\(/super().__init__(/g;
        $line =~ s/(\W)'h([a-fA-F0-9]+)/$1 0x$2/g;
        $line =~ s/(\W)'b([01]+)/$1 0b$2/g;
        $line =~ s/(\W)'([0-9]+)/$1 $2/g;
        $line =~ s/&&/ and /g;
        $line =~ s/!==/!=/g;
        $line =~ s/\|\|/ or /g;
        $line =~ s/forever\s+begin/while True:/g;

        if ($line =~ /^(\s*)\@\s*\((\w+\s+)?\s*(.*)\)/) {
            my $edge = $2;
            my $sig = $3;
            my $ii = "";
            $ii = $1 if defined $1;
            $add_line = 0;
            if (defined $edge) {
                $edge = $edge eq 'posedge' ? "RisingEdge" : "FallingEdge";
            }
            else {
                $edge = "Edge";
            }
            push(@outfile, "$ws#${ii}yield $edge($sig)\n");
            add_import(\@imports, "from cocotb.triggers import *\n");

        }

        # Imports are added here
        if ($line =~ /`uvm_(component|object)_utils/) {
            add_import(\@imports, "from uvm.macros import *\n");
        }
        elsif ($line =~ /extends uvm_(\w+)/) {
            my $imp_name = "uvm.base.uvm_$1";
            if (exists $pkg_map->{"uvm_$1"}) {
                $imp_name = $pkg_map->{"uvm_$1"};
            }
            add_import(\@imports, "from $imp_name import *\n");
        }


        # Replace standard UVM functions
        $line =~ s/(virtual)? function void build\(\)/$def_build_phase/g;
        $line =~ s/(virtual)? function void connect\(\)/$def_build_phase/g;
        $line =~ s/(virtual)? function void connect_phase\(uvm_phase phase\)/$def_conn_phase/g;
        $line =~ s/(virtual)? function void build_phase\(uvm_phase phase\)/$def_build_phase/g;
        $line =~ s/class (\w+) extends (\w+)/class $1($2):/g;

        # SystemVerilog functions
        $line =~ s/\$(urandom|random|sformatf|cast|display)\b/sv.$1/g;

        if ($line =~ $conf_db_re) {
            $line =~ s/$conf_db_re/UVMConfigDb.$1/g;
            add_import(\@imports, "from uvm.base.uvm_config_db import *\n");
        }
        if ($line =~ $res_db_re) {
            $line =~ s/$res_db_re/UVMResourceDb.$1/g;
            add_import(\@imports, "from uvm.base.uvm_resource_db import *\n");
        }

        $line =~ s/(virtual\s+)?(protected\s+)?task\s+(\w+)\s*\(/def $3(self,/g;

        $line =~ s/super\.(\w+)_phase(phase)/super().$1_phase(phase)/g;
        $line =~ s/uvm_component parent = None/parent=None/g;
        $line =~ s/phase\(self,\s*uvm_phase\s+phase\s*\)$/phase(self, phase):/g;

        if ($IN_CLASS) {
            $line =~ s/function (.*)\((.*)\)/def $1(self,$2):/g;
            $line =~ s/task (.*)\((.*)\)/def $1(self,$2):  # task/g;
        }


        # Final trimmings due to bad substitutions
        $line =~ s/\(self,\)/(self)/g;
        $line =~ s/,\s*uvm_component parent/, parent/g;

        if ($add_line) {
            push(@outfile, "$ws#$line");
        }

        if ($line =~ /^class /) {
            ++$ind;
            $st = $IN_CLASS;
        }
        elsif ($line =~ /^endclass/) {
            --$ind;
            if ($ind < 0) {$ind = 0;}
            $st = $GLOBAL;
        }
    }

    splice(@outfile, $new_endfunction, 0, @found_vars);
    # Add imports to the import line

    my $chosen_line = $import_line == -1 ? $include_line : $import_line;
    splice(@outfile, $chosen_line, 0, @imports);

    if ($st != $GLOBAL) {
        print("Warning! File $fname did not finish to global state\n");
    }

    my @new_array;
    if ($is_py) {
        for my $line (@outfile) {
            $line =~ s/^#//;
            push(@new_array, $line);
        }
    }

    close($IFILE);
    if ($is_py) {
        return  wantarray ? @new_array : join('', @new_array );
    }
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

# Add safer check, ie if file would be overwritten
sub is_safe_to_write {
    my ($py_file) = @_;
    my $ok = system("git ls-files --error-unmatch $py_file >& /dev/null");
    if ($ok != 0) {return 1;}
    print ("File $py_file under git, and will not be overwritten\n");
    return 0;
}

sub add_import {
    my ($aref, $imp) = @_;
    my $found = 0;
    for my $f (@{$aref}) {
        if ($f eq $imp) {
            $found = 1;
        }
    }
    if ($found == 0) {
        push(@{$aref}, $imp);
    }
}
