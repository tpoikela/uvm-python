#!/usr/bin/env perl
#===============================================================================
#
#         FILE: status.pl
#
#        USAGE: ./status.pl
#
#  DESCRIPTION: 
#
#      OPTIONS: ---
#       AUTHOR: Tuomas Poikela (tpoikela), tuomas.sakari.poikela@gmail.com
# ORGANIZATION: ----
#      VERSION: 0.1
#      CREATED: 01/11/2020 09:23:56 AM
#===============================================================================

use strict;
use warnings;
use utf8;

use Getopt::Long;
use Pod::Usage;

package FileInfo;

sub new {
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $href = shift;

    my $self = {
        name => '',
        lineno => 0,
        lines => 0,
        sv_todo => 0,
        py_done => 0,
    };
    bless($self, $class);

    if (defined $href) {
        for my $key (keys %{$href}) {
            $self->{$key} = $href->{$key};
        }
    }
    return $self;
}

1;

package Parser;

sub new {
    my $proto = shift;
    my $class = ref($proto) || $proto;

    my $self = {
        curr_class => undef,
        curr_func => undef,
        lang => '',
        re => {}
    };
    bless($self, $class);

    $self->_init_re();
    return $self;
}

sub set_file {
    my ($self, $fname) = @_;
    $self->{fname} = $fname;
    $self->{files}->{$fname} = FileInfo->new({
        name => $fname,
        lineno => 1,
    });
}

sub incr {
    my ($self, $key) = @_;
    $self->{num}->{$key} += 1;
    my $fname = $self->{fname};
    $self->{files}->{$fname}->{$key} += 1;
}

sub parse_line {
    my ($self, $line) = @_;
    # SV line in comments
    if ($self->is_empty($line)) {
        $self->incr('empty');
    }
    elsif ($self->is_possibly_sv($line)) {
        # If #| or # // then skip the line
        if ($line !~ /^\s*#\s*(\||\/\/)/) {
            $self->process_sv($line);
        }
        $self->incr('commented');
    }
    else {  # Python line
        $self->process_py($line);
    }

    my $fname = $self->{fname};
    $self->{files}->{$fname}->{lineno} += 1;
    $self->incr('lines');
}

sub is_possibly_sv {
    my ($self, $line) = @_;
    if ($self->{lang} ne 'py' or $self->{flags}->{is_func} == 0) {
        return $line =~ $self->{re}->{comment};
    }
}

sub is_empty {
    my ($self, $line) = @_;
    if ($self->{flags}->{is_func} == 0) {
        return $line =~ $self->{re}->{empty};
    }
    return $line =~ /^$/;
}

# Main function for SV processing
sub process_sv {
    my ($self, $line) = @_;
    $self->{lang} = "sv";
    $self->{rules} = $self->{re}->{sv};
    $self->process_line_with_rules($line);
    #if ($self->{flags}->{is_func} == 1) {
    #    $self->incr('sv_todo');
    #}
    $self->incr('sv_todo');
    #print "SV_LINE |$line|";
}

# Main function for Python processing
sub process_py {
    my ($self, $line) = @_;
    $self->{lang} = "py";
    $self->{rules} = $self->{re}->{py};
    $self->process_line_with_rules($line);
    if ($self->{flags}->{is_func} == 1) {
        $self->incr('py_done');
    }
}

sub process_line_with_rules {
    my ($self, $line) = @_;
    my $match = 0;
    for my $rule (@{$self->{rules}}) {
        #my $rule = $self->{rules}->{$key};
        if ($self->pred_ok($rule)) {
            if ($self->match_ok($rule, $line)) {
                $self->set_flags($rule);
                if (exists $rule->{action}) {
                    $rule->{action}->($self);
                }
                last;
            }
        }
    }
}

# Checks if predicates for the rule are OK. Returns 1 if there
# are no predicates.
sub pred_ok {
    my ($self, $rule) = @_;
    return 1 if not exists $rule->{pre}; # No predicates
    for my $pre (@{$rule->{pre}}) {
        if ($pre =~ /!(\w+)/) {
            if (exists $self->{flags}->{$pre}) {
                if ($self->{flags}->{$pre} == 1) {
                    return 0;
                }
            }
        }
        else {
            if (not exists $self->{flags}->{$pre}) {
                return 0;
            }
            if ($self->{flags}->{$pre} == 0) {
                return 0;
            }
        }
    }
    my $rulename = $rule->{name};
    $self->msg("All pred match for $rulename");
    return 1;
}

sub match_ok {
    my ($self, $rule, $line) = @_;
    my @matches = ($line =~ qr/$rule->{re}/);
    my $num_match = int(@matches);
    if ($num_match > 0) {
        my $rule_name = $rule->{name};
        #$self->msg("Matches are |" . join(',', @matches) . "| for line $line, rule: $rule_name");
        if (exists $rule->{capt}) {
            my $num_capt = int(@{$rule->{capt}});
            #if ($num_capt != int(@matches)) {
            #    $self->msg("ERR. num_capt: $num_capt != num_match: $num_match"
            #        . ", rule: $rule_name");
            #}
            for (my $i = 0; $i < $num_capt; ++$i) {
                next if not defined $matches[$i];
                my $capt_name = $rule->{capt}->[$i];
                $self->{capt}->{$capt_name} = $matches[$i];
                $self->msg("Captured |$capt_name| = " .
                    $self->{capt}->{$capt_name});

            }
        }
        return 1;
    }
    return $line =~ qr/$rule->{re}/;
}

sub set_flags {
    my ($self, $rule) = @_;
    if (exists $rule->{flags}) {
        for my $flag ( @{$rule->{flags}} ) {
            if ($flag =~ /!(\w+)/) {
                $self->{flags}->{$1} = 0;
                $self->msg("Flag |$1| set to 0");
            }
            else {
                $self->{flags}->{$flag} = 1;
                $self->msg("Flag |$flag| set to 1");
            }
        }
    }
}

sub reset_num {
    my ($self) = @_;
    $self->{num} = {
        commented => 0,
        sv_todo => 0,
        py_done => 0,
        lines => 0,
        empty => 0,
        py => 0,
        sv => 0
    };
}

sub reset_flags {
    my ($self) = @_;
    $self->{flags} = {
        is_func => 0,
        is_class => 0
    };
}


sub _init_re {
    my ($self) = @_;

    my $re_qual = qr/(virtual|protected|local|static)*/;
    my $ret_val = qr/(.*)/;

    $self->reset_num();
    $self->reset_flags();

    $self->{classes} = {
        func => {}
    };

    $self->{re}->{comment} = qr/^\s*#/;
    $self->{re}->{empty} = qr/^\s*#?\s*$/;

    $self->{re}->{sv} = [
        # Format is regex to match, precondition, flags to set, captures
        {
            name => 'sv_func_start',
            re => qr/$re_qual\s*(function|task)\s*$ret_val?(\w+::)?(\w+)\s*\(/,
            pre => [], 
            flags => ['is_func'], 
            capt => ['qualifier', 'func_or_tas', 'return', 'class', 'name'],
            #action => sub {print "XYZ Action done\n"}
        },
        {
            name => 'sv_func_end',
            re => qr/^\s*#\s*endfunction/,
            pre => ['is_func'],
            flags => ['!is_func'], 
            capt => []
        },
        {
            name => 'sv_class_start',
            re => qr/^#\s*class\s+(\w+)(\s+extends\s+(\w+))?/,
            pre => [],
            flags => ['is_class'], 
            capt => ['name', 'extends', 'base'],
            action => sub {
                my ($self) = @_;
                my $classname = $self->{capt}->{name};
                $self->{curr_class} = $classname;
                $self->{classes}->{$classname} = {};
            }
        },
        {
            name => 'sv_class_end',
            re => qr/^#\s*endclass/,
            pre => ['is_class'],
            flags => ['!is_class'], 
            capt => []
        },
    ];

    $self->{re}->{py} = [
        # Format is regex to match, precondition, flags to set, captures
        {
            name => 'py_func_start',
            re => qr/^\s+def (\w+)\s*\(/,
            pre => ['is_class'], 
            flags => ['is_func'], 
            capt => ['name']
        },
        {
            name => 'py_func_end',
            re => qr/^    \S.*$/,
            pre => ['is_func'], 
            flags => ['!is_func'],
            capt => []
        },
        {
            name => 'py_class_start',
            re => qr/^class\s+(\w+)\(?(\w+)\):/,
            flags => ['is_class'],
            capt => ['name', 'base']
        },
        {
            name => 'py_class_end',
            re =>qr/^$/,
            pre => ['is_class'], 
            flags => ['!is_class'],
            capt => []
        },
    ];

    $self->{quiet} = 1;
    $self->{show_completed} = 0;
}

sub msg {
    my ($self, $msg) = @_;
    return if $self->{quiet};
    my $fname = $self->{fname};
    my $line = $self->{files}->{$fname}->{lineno};
    print("[L$line $fname]: " . $msg . "\n");
}

sub curr_line {
    my ($self) = @_;
    my $fname = $self->{fname};
    return $self->{files}->{$fname}->{lineno};
}

sub print_info {
    my ($self) = @_;
    for my $fname (sort keys %{$self->{files}}) {
        my $file_info = $self->{files}->{$fname};
        my $py = $file_info->{py_done};
        my $tot = $py + $file_info->{sv_todo};
        if ($tot > 0) {
            my $perc = 100 * $py / $tot;
            if ($perc < 100 or $self->{show_completed} == 1) {
                print "$fname: $perc% ($py/$tot) completed\n";
            }
        }
    }
    print "\nSummary of all files:\n";
    my $py = $self->{num}->{py_done};
    my $tot = $py + $self->{num}->{sv_todo};
    for my $key (sort keys %{$self->{num}}) {
        print("$key: " . $self->{num}->{$key} . "\n");
    }
    if ($tot > 0) {
        my $perc = 100 * $py / $tot;
        print "TOTAL: $perc% ($py/$tot) completed\n";
    }

}

1;

#---------------------------------------------------------------------------
# MAIN
#---------------------------------------------------------------------------

package main;

my %opt;
GetOptions(
    # Standard arguments
    "d|debug"   => \$opt{debug},
    "f=s"       => \$opt{f},
    "help|?"    => \$opt{help},
    "man"       => \$opt{man},
    "o=s"       => \$opt{o},
    "q|quiet"   => \$opt{quiet},
    "v|verbose" => \$opt{verbose},

    # Custom arguments
    <+opt1+> => \$opt{<+val1+>},
    <+opt2+> => \$opt{<+val2+>},
);

pod2usage(1) if $opt{help};
pod2usage(-exitval => 0, -verbose => 2) if $opt{man};

my @files = @ARGV;

my $py_data = create_data();
my $sv_data = create_data();
my $P = Parser->new();

foreach my $f (@files) {
    #_msg("Processing now file $f");
    process_file($f, $sv_data, $py_data);
}

$P->print_info();

#-----------------------------------------------------------------------------
# Internal helper functions (autogenerated)
#-----------------------------------------------------------------------------

sub process_file {
    my ($fname, $sv, $py) = @_;
    my $data = {
        sv => $sv,
        py => $py
    };
    open(my $IFILE, "<", $fname) or die $!;
    $P->set_file($fname);
    while (<$IFILE>) {
        my $line = $_;
        $P->parse_line($line);
    }
    $P->reset_flags();
    close($IFILE);
}

sub create_data {
    my $href = {
        func => {}
    };
}

# For printing debug information
sub _debug {
    my ($msg) = @_;
    print "status.pl [DEBUG] $msg\n" if $opt{debug};
}

# For printing out messages if not quiet
sub _msg {
    my ($msg) = @_;
    print "status.pl $msg\n" unless $opt{quiet};
}

# For printing error information
sub _error {
    my ($msg) = @_;
    print STDERR "status.pl [ERROR]$msg\n";
}

__END__
=head1 NAME

=head1 SYNOPSIS

status.pl [options]

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
