#! /usr/bin/env perl

use strict;

my $build_cmd = "python -m build";
my $twine_cmd = "python -m twine upload --repository testpypi dist/*";

my $err = system($build_cmd);
if ($err == 0) {
    system($twine_cmd);
}
else {
    die("$build_cmd failed. Not uploading to PyPi");
}
