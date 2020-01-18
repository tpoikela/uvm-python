# Contributor's Guide

1. Follow the [Contribution Guidelines](#contribution-guidelines) to initially set up the project.

## Contribution Guidelines

- [Prerequisites](#prerequisites)

### Prerequisites

| Prerequisite                                | Version    |
| ------------------------------------------- | -------    |
| Python                                      | `~ ^3`     |
| iverilog                                    | `~ ^11`    |
| cocotb                                      | `~ ^1.2`   |
| cocotb-coverage                             | `~ ^1.0.0` |


See also `.gitlab-ci.yml` for tips for installation.

### Forking The Project

#### Forking /uvm-python

1. Go to the top level /uvm-python repository: <https://github.com/tpoikela/uvm-python>
2. Click the "Fork" Button in the upper right hand corner of the interface ([More Details Here](https://help.github.com/articles/fork-a-repo/))
3. After the repository has been forked, you will be taken to your copy of the
uvm-python repo at `yourUsername/uvm-python`

#### Cloning Your Fork

1. Open a Terminal / Command Line / Bash Shell in your projects directory (_i.e.: `/yourprojectdirectory/`_)
2. Clone your fork of uvm-python

```shell
$ git clone https://github.com/yourUsername/uvm-python.git
```

##### (make sure to replace `yourUsername` with your GitHub Username)

This will download the entire uvm-python repo to your projects directory.

#### Setup Your Upstream

1. Change directory to the new uvm-python directory (`cd uvm-python`)
2. Add a remote to the official uvm-python repo:

```shell
$ git remote add upstream https://github.com/tpoikela/uvm-python.git
```

Congratulations, you now have a local copy of the uvm-python repo!

#### Maintaining Your Fork

Now that you have a copy of your fork, there is work you will need to do to keep it current.

##### **Rebasing from Upstream**

Do this prior to every time you create a branch for a PR:

1. Make sure you are on the `master` branch

  > ```shell
  > $ git status
  > On branch master
  > Your branch is up-to-date with 'origin/master'.
  > ```

  > If your aren't on `master`, resolve outstanding files / commits and checkout the `master` branch

  > ```shell
  > $ git checkout master
  > ```

2. Do a pull with rebase against `upstream`

  > ```shell
  > $ git pull --rebase upstream master
  > ```

  > This will pull down all of the changes to the official master branch, without making an additional commit in your local repo.

3. (_Optional_) Force push your updated master branch to your GitHub fork

  > ```shell
  > $ git push origin master --force
  > ```

  > This will overwrite the master branch of your fork.

### Create A Branch

Before you start working, you will need to create a separate branch specific to the issue / feature you're working on. You will push your work to this branch.

#### Naming Your Branch

Name the branch something like `fix/xxx` or `feature/xxx` where `xxx` is a short description of the changes or feature you are attempting to add. For example `fix/email-login` would be a branch where you fix something specific to email login.

#### Adding Your Branch

To create a branch on your local machine (and switch to this branch):

```shell
$ git checkout -b [name_of_your_new_branch]
```

and to push to GitHub:

```shell
$ git push origin [name_of_your_new_branch]
```

### Make Changes

There are several possibilities to work on:

  1. Create a unit test. Look at the source files in `uvm/` folder. If
     corresponding test file exists in `unit/test_???.py`, you can add a unit test
     for untested function. If there is no file, you can create a new unit test 
     file and add your tests there. 
  2. There is lot of commented code still in `uvm/**` folders, in Python files.
     Take one function, and port it to working Python. Make sure to add a unit 
     test for the function if possible (See 1.)
  3. Look at more complex examples in `test/examples`. You can take one of them,
     and port it to Python. Take a look at the existing working examples as
     starting point. You can reuse `Makefile` from them.
  4. If you can think of any Makefile/workflow/CI or other improvements, those
     are welcome too.
  5. 

### Run The Test Suite

When you're ready to share your code, run the test suite:

```shell
$ make test
# Or just unit tests
$ make test-unit
```

and ensure all tests pass.

### Squash Your Commits

When you make a pull request, all of your changes can be squashed to one commit.
If you have made more than one commit, then you can _squash_ your commits.

To do this, see [Squashing Your Commits](http://forum.freecodecamp.com/t/how-to-squash-multiple-commits-into-one-with-git/13231).

### Creating A Pull Request

#### What is a Pull Request?

A pull request (PR) is a method of submitting proposed changes to the uvm-python
Repo (or any Repo, for that matter). You will make changes to copies of the
files which make up uvm-python in a personal fork, then apply to have them
accepted by uvm-python proper.

