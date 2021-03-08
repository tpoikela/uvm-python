#! /usr/bin/env perl

use strict;

use Getopt::Long;

my %opt;
GetOptions(
    "production" => \$opt{production},
    "clean" => \$opt{clean},
);

if (defined $opt{clean}) {
    system("rm dist/*") if -d "./dist";
}

my $build_cmd = "python -m build";
my $twine_cmd = "python -m twine upload --repository testpypi dist/*";
if ($opt{production}) {
    $twine_cmd = "python -m twine upload dist/*";
}

my $err = system($build_cmd);
if ($err == 0) {
    system($twine_cmd);
}
else {
    die("$build_cmd failed. Not uploading to PyPi");
}
