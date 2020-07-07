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
#      OPTIONS: -f <FILE>, -all, -d|debug, --author <NAME>, -p, -f
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

use Pod::Usage;
use Getopt::Long;
use File::Basename;
use File::Spec;
use Data::Dumper;

package SV2PyReplacer;

sub new {
    my $proto = shift;
    my $class = ref($proto) || $proto;

    my $self = {};
    bless($self, $class);


    $self->{re} = {};
    $self->{re}->{func_phases} =
        qr/(build|connect|end_of_elaboration|end_of_simulation|extract|check|report|final)/;
    $self->{re}->{task_phases} = qr/(reset|configure|main|run)/;
    return $self;
}

sub do_simple_subst {
    my ($self, $line) = @_;
    $$line =~ s/(\w+)'\((.*)\);/$2  # cast to '$1' removed/g;
    $$line =~ s/;$//g;  # Remove trailing semicolon
    $$line =~ s/\s*==\s*null/ is None/g;
    $$line =~ s/\s*!=\s*null/ is not None/g;
    $$line =~ s/\bnull\b/None/g;
    $$line =~ s/\bthis\b/self/g;
    $$line =~ s/\) begin\b/):/g;
    $$line =~ s/\belse\s+if\b/elif/g;
    $$line =~ s/function new\s*\(\s*string name/def __init__(self, name/g;
    $$line =~ s/::type_id::create/.type_id.create/g;
    $$line =~ s/super\.new\(/super().__init__(/g;
    $$line =~ s/(\W)'h([a-fA-F0-9]+)/$1 0x$2/g;
    $$line =~ s/(\W)'b([01]+)/$1 0b$2/g;
    $$line =~ s/(\W)'([0-9]+)/$1 $2/g;
    $$line =~ s/&&/ and /g;
    $$line =~ s/!==/!=/g;
    $$line =~ s/\|\|/ or /g;
    $$line =~ s/forever\s+begin/while True:/g;
    $$line =~ s/self file except/this file except/g;
    $$line =~ s/repeat\((\w+)\)/for i in range($1)/g;
    $$line =~ s/^\s*import (\w+)::\*/from $1 import */g;

    # We don't want to match ## here because it's different operator than #
    $$line =~ s/(?<!#)#(\w+)(ms|us|ns|ps|fs)?/yield Timer($1, $2)/g;
}

sub do_sv_uvm_subts {
    my ($self, $line) = @_;
    my $re_func_phases = $self->{re}->{func_phases};
    my $re_task_phases = $self->{re}->{task_phases};
    # Replace standard UVM functions
    $$line =~ s/(virtual)?\s+function\+svoid\s+$re_func_phases\(.*\)/def $1(self, phase):/g;
    $$line =~ s/(virtual)?\s+task\s+$re_task_phases\(.*\)/def $1(self, phase):/g;
    $$line =~ s/class\s+(\w+)\s+extends\s+(\w+)/class $1($2):/g;
    $$line =~ s/super\./super()./g;

    # SystemVerilog functions
    $$line =~ s/\$(urandom|random|sformatf|bits|cast|display)\b/sv.$1/g;

    $$line =~ s/(virtual\s+)?(protected\s+)?task\s+(\w+)\s*\(/def $3(self,/g;
    $$line =~ s/super\.(\w+)_phase(phase)/super().$1_phase(phase)/g;
    $$line =~ s/uvm_component parent = None/parent=None/g;
    $$line =~ s/phase\(self,\s*uvm_phase\s+phase\s*\)$/phase(self, phase):/g;
    $$line =~ s/`uvm_(info|warning|fatal|error)\(/uvm_$1(/g;
}


1;

# Stores info about classes found, such as name, start_line etc
package ClassInfo;

sub new {
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $href = shift;

    my $self = {
        name => '',
        start_line => 0,
        end_line => 0,
        base => 0,
        new_start => 0,
        new_end => 0,
        var => {},
        func => {}
    };
    bless($self, $class);

    if (defined $href) {
        for my $key (keys %{$href}) {
            $self->{$key} = $href->{$key};
        }
    }
    return $self;
}

sub add_var {
    my ($self, $name, $type) = @_;
    $self->{var}->{$name} = $type;
}


1;

package main;

my $DEBUG = 0;

my %opt;
GetOptions(
    "file|f=s" => \$opt{f},
    "all"      => \$opt{all},
    "d|debug"  => \$DEBUG,
    "author=s" => \$opt{author},
    "p|print"  => \$opt{print},
    "f|force"  => \$opt{force},
    "h|help"   => \$opt{help},
    "man"       => \$opt{man},
    "q|quiet"   => \$opt{quiet},
    "v|verbose" => \$opt{verbose},
);

pod2usage(1) if $opt{help};
pod2usage(-exitval => 0, -verbose => 2) if $opt{man};

my $AUTHOR = $opt{author} || "Tuomas Poikela (tpoikela)";

#---------------------------------------------------------------------------
# REGULAR EXPRESSIONS
#---------------------------------------------------------------------------

my $re_qual = qr/(protected|local)/; # $1
my $re_type = qr/(\w+(#\(\w+\))?)/;  # $2, $3, $4
my $re_packed = qr/(\[.*\])?/;       # $5
my $re_name = qr/(\w+)/;             # $6
my $re_unpacked = qr/((\[.*\])+)/;   # $7, $8 (full)
my $re_init_var = qr/(=[^;]+)/;      # $9

my $re_var = qr/(rand)?$re_qual?\s*$re_type\s*$re_packed\s*$re_name\s*$re_unpacked?$re_init_var?\s*;\s*$/;
my $re_new_call = qr/(\w+)\s*=\s*new\s*\(/;

my $conf_db_re = qr/uvm_config_db#\(.*\)::(set|get)/;
my $conf_db_re2 = qr/uvm_config_(int|string|object)::(set|get)/;
my $res_db_re = qr/uvm_resource_db#\(.*\)::(set|get)/;
my $edge_re = qr/^(\s*)\@\s*\((\w+\s+)?\s*(.*)\)/;

my $GLOBAL = 1 << 0;
my $IN_CLASS = 1 << 1;
my $IN_NEW = 1 << 2;
my $IN_TASK = 1 << 3;
my $IN_FUNC = 1 << 4;
my $IN_COMMENT = 1 << 5;
my $IN_COVERGROUP = 1 << 6;

#---------------------------------------------------------------------------
# GLOBAL VARS
#---------------------------------------------------------------------------

# Store info about classes
my $all_classes = {};

my $st = $GLOBAL;

my @suffixlist = ('.py', '.sv', '.svh');

my @files = ();
my $pkg_map = build_pkg_map();

#---------------------------------------------------------------------------
# MAIN SCRIPT
#---------------------------------------------------------------------------

# Find files to process first, and put them into array
if (defined $opt{f} and -e $opt{f}) {
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

if ($DEBUG != 0) {
    print "Dumping found class information:\n";
    print Dumper($all_classes);
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
        print STDERR "Parsing file without suffix not supported. File: $fname\n";
    }

    my @outfile = ();
    my $ind = 0;
    my $def_conn_phase = "def connect_phase(self, phase):";
    my $def_build_phase = "def build_phase(self, phase):";

    my $new_endfunction = {}; # For each class
    my $import_line = -1;
    my $include_line = -1;
    my $ifndef_line = -1;

    my $curr_class = '';
    my @imports = ();

    my $found_vars = {};
    my $has_author = $is_py;  # Do not re-insert to py files
    my @classes_file = ();

    my $sv2py = SV2PyReplacer->new();

    while (<$IFILE>) {
        my $line = $_;
        my $ws = " " x (4 * $ind);
        ++$lineno;
        my $add_line = 1;  # If set to 0, skip adding this line to file

        # In .py files, skip uncommented lines to avoid overwriting modifications
        if ($is_py and $line !~ /^\s*#/) {
            push(@outfile, $line);
            next;
        }

        # Skip commented in SV files
        if ($is_py == 0 && $line =~ m{^\s*//} && $has_author) {
            push(@outfile, "$ws#$line");
            next;
        }
        elsif ($line =~ m{^\s*/\*}) {
            push(@outfile, "$ws#$line");
            set_state($IN_COMMENT);
            next;
        }
        elsif ($line =~ m{\*/}) {
            clear_state($IN_COMMENT);
        }

        # Look for line in which imports start, alternatively find 1st include
        # or ifndef
        if ($import_line == -1 && $line =~ /^\s*import /) {
            $import_line = $lineno;
        }
        elsif ($include_line == -1 && $line =~ /^\s*`include/) {
            $include_line = $lineno;
        }
        elsif ($ifndef_line == -1 && $line =~ /^\s*`ifndef/) {
            $ifndef_line = $lineno;
        }

        # Add author name, use -author "My Name"
        if ($line =~ /^(.*)All rights reserved worldwide/i) {
            my $cline = "#$1Copyright 2019-2020 $AUTHOR\n";
            $has_author = 1;
            push(@outfile, $cline);
        }

        # Check for various tasks and functions
        if ($line =~ /^\s*(virtual\s+)?(protected\s+)?task\s+(\w+)/) {
            my $task_name = $1;
            set_state($IN_TASK);
            push(@outfile, "$ws#async\n");
        }
        elsif ($line =~ /^\s*endtask/) {
            clear_state($IN_TASK);
        }
        elsif ($line =~ /^\s*(virtual\s+)?(protected\s+)?function\s+(\w+)/) {
            my $func_name = $1;
            set_state($IN_FUNC);
        }
        elsif ($line =~ /^\s*endfunction/) {
            clear_state($IN_FUNC);
        }

        # Inside class but not in task/function/group, finds member variables
        if ($st == $IN_CLASS) {
            if ($line !~ m{^\s*//} && $line =~ $re_var) {
                my $value = "None";
                my $var_type = $3;
                my $var_name = $6;
                my $unpacked = $8;
                my $var_init = $9;

                $all_classes->{$curr_class}->add_var($var_name, $var_type);

                if ($var_type =~ /\bint(eger)?\b/ ) {$value = 0;}
                if ($var_type =~ /\bstring\b/ ) {$value = "";}
                if (defined $var_init) {
                    $value = $var_init;
                    $value =~ s/=//;
                }
                my $self_var = "${ws}#    self.$var_name = $value  # type: $var_type\n";
                push(@{$found_vars->{$curr_class}}, $self_var);
            }
        }

        # Finds if we're entering a class, or getting out of it
        if ($line =~ /^\s*(virtual\s+)?class\s+(\w+)/) {
            ++$ind;
            $st = $IN_CLASS;
            $curr_class = $2;
            $found_vars->{$curr_class} = [];
            my $class_info = ClassInfo->new({
                name => $2,
                start_line => $lineno
            });
            $all_classes->{$2} = $class_info;
        }
        elsif ($line =~ /^\s*endclass/) {
            --$ind;
            if ($ind < 0) {$ind = 0;}
            $st = $GLOBAL;
        }

        # Finds new call like 'a = new()' and changes it to 'self.a = MyClass()'
        if ($line =~ $re_new_call) {
            my $var_name = $1;
            my $var_data = $all_classes->{$curr_class}->{var};
            if (exists $var_data->{$var_name}) {
                my $var_type = $var_data->{$var_name};
                $line =~ s/$re_new_call/self.$var_name = $var_type(/;
            }

        }

        # Finds where new declaration starts
        if ($line =~ /function\s+(\w+::)?new\s*\(/) {
            set_state($IN_NEW);
            $all_classes->{$curr_class}->{new_start} = $lineno;
        }
        elsif (($st & $IN_NEW) && $line =~ /endfunction/) {
            $new_endfunction->{$curr_class} = $lineno;
            $all_classes->{$curr_class}->{new_end} = $lineno;
            clear_state($IN_NEW);
        }

        $sv2py->do_simple_subst(\$line);


        if ($line =~ $edge_re) {
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
        if ($line =~ /`uvm_(component|object)(_param)?_utils/) {
            add_import(\@imports, "from uvm.macros import *\n");
        }
        elsif ($line =~ /extends uvm_(\w+)/) {
            my $imp_name = "uvm.base.uvm_$1";
            if (exists $pkg_map->{"uvm_$1"}) {
                $imp_name = $pkg_map->{"uvm_$1"};
            }
            $all_classes->{$curr_class}->{base} = "uvm_$1";
            add_import(\@imports, "from $imp_name import *\n");
        }

        $sv2py->do_sv_uvm_subts(\$line);

        # Config/Resource Db replacements
        if ($line =~ $conf_db_re) {
            $line =~ s/$conf_db_re/UVMConfigDb.$1/g;
            add_import(\@imports, "from uvm.base.uvm_config_db import *\n");
        }
        elsif ($line =~ $conf_db_re2) {
            $line =~ s/$conf_db_re2/UVMConfigDb.$2/g;
            add_import(\@imports, "from uvm.base.uvm_config_db import *\n");
        }
        elsif ($line =~ $res_db_re) {
            $line =~ s/$res_db_re/UVMResourceDb.$1/g;
            add_import(\@imports, "from uvm.base.uvm_resource_db import *\n");
        }

        if ($IN_CLASS) {
            $line =~ s/function (.*)\((.*)\)/def $1(self,$2):/g;
            $line =~ s/task (.*)\((.*)\)/def $1(self,$2):  # task/g;
        }

        do_coverage_subst(\$line, $lineno);

        #--------------------------------------------------
        # Final trimmings due to bad substitutions
        #--------------------------------------------------
        do_final_trimmings(\$line);

        if ($add_line) {
            push(@outfile, "$ws#$line");
        }
    }

    foreach my $cls (@classes_file) {
        splice(@outfile, $new_endfunction->{$cls}, 0,
            $found_vars->{$cls});
    }

    # Add imports to the import line
    my $chosen_line = $import_line == -1 ? $include_line : $import_line;
    splice(@outfile, $chosen_line, 0, @imports);

    if ($st != $GLOBAL) {
        print("Warning! File $fname did not finish to global state\n");
    }

    # Used only for re-runs of .py files
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

sub do_coverage_subst {
    my ($line, $lineno) = @_;
    if ($$line =~ /covergroup\s+(\w+)/) {
        set_state($IN_COVERGROUP);
        $$line =~ s/covergroup\s+(\w+)/$1 = coverage_section(/g;
    }
    elsif ($$line =~ /endgroup/) {
        clear_state($IN_COVERGROUP);
        $$line =~ s/\bendgroup\b/) # Close coverage section/g;
    }
    elsif (in_state($st, $IN_COVERGROUP) > 0) {
        $$line =~ s/(\w+)\s*:\s*cross/\@CoverCross('$1', items = [/g;
        #$$line =~ s/cross/\@CoverCross/;
        $$line =~ s/(\w+): coverpoint/\@CoverPoint('$1', xf = lambda a: a, bins = []) # /;
    }
}

# Creates a simple py pkg map to add imports automatically to the file
sub build_pkg_map {
    my @py_sources = ();
    if (exists $ENV{UVM_PYTHON}) {
        @py_sources = glob("$ENV{UVM_PYTHON}/uvm/**/*.py");
    }
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
                print "$p not matching yet\n" if $DEBUG;
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

sub in_state {
    my ($st, $state) = @_;
    my $res = ($st & $state);
    return $res != 0;
}

sub set_state {
    my ($new_state) = @_;
    $st = $st | $new_state;
}

sub clear_state {
    my ($new_state) = @_;
    $st = $st & ~$new_state;
}

sub do_final_trimmings {
    my ($line) = @_;
    $$line =~ s/\(self,\)/(self)/g;
    $$line =~ s/,\s*uvm_component parent/, parent/g;
    $$line =~ s/virtual def \w+ (\w+)\(/def $1(/g;
    $$line =~ s/self,\s*uvm_phase\s+phase/self, phase/g;
    # Remaining func return type
    $$line =~ s/def (\w+) (\w+)\s*\(/def $2(/g;
    $$line =~ s/virtual def/def/g;
}



#-----------------------------------------------------------------------------
# Internal helper functions (autogenerated)
#-----------------------------------------------------------------------------

# For printing debug information
sub _debug {
    my ($msg) = @_;
    print "sv2py.pl [DEBUG] $msg\n" if $opt{debug};
}

# For printing out messages if not quiet
sub _msg {
    my ($msg) = @_;
    print "sv2py.pl $msg\n" unless $opt{quiet};
}

# For printing error information
sub _error {
    my ($msg) = @_;
    print STDERR "sv2py.pl [ERROR]$msg\n";
}

__END__
=head1 NAME

=head1 SYNOPSIS

sv2py.pl [options]

  Options:
    -d|debug    Turn on all debugging features.
    -f          Input file.
    -help       Print help message.
    -man        Bring up man-pages of the script.
    -o          Output file.
    -q|quiet    Run script in quiet mode (no std out).
    -v|verbose  Run script in verbose mode (more std out).

=head1 OPTIONS

=over 8

=item B<-d|debug>

Turns on all debugging features.

=item B<-f> <filename>

Name of the input file.

=item B<-help>

Prints help message.

=item B<-man>

Shows the man-pages.

=item B<-o> <filename>

Output file name.

=item B<-q|quiet>

Runs script in quiet mode.

=item B<-v|verbose>

Runs script in verbose mode.

=back

=head1 DESCRIPTION

Describe the script here.

=head1 AUTHOR

    Written by Tuomas Poikela, tuomas.sakari.poikela@gmail.com

=cut
