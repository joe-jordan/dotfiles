#!/usr/bin/python2.7
# -*- coding: ascii -*-

import os
import os.path
import errno
import shutil


def logger(func):
    """decorator to turn `func` into a logger function of the same name.
    :param func: python callable.
    :return a new python callable."""
    prefix = func.func_name.upper() + ":"

    def impl(message):
        """ logger function
        :param message: str *message to log.*"""
        print prefix, message
        func(message)
    impl.__doc__ = prefix + impl.__doc__
    impl.func_name = func.func_name
    return impl


@logger
def info(_):
    """info"""
    pass


@logger
def warn(_):
    """warn"""
    pass


@logger
def error(_):
    """error"""
    pass


@logger
def fatal(_):
    """fatal"""
    exit(1)


# alias some stdlib functions for manipulating symlinks:
is_symlink = os.path.islink
symlink_target = os.path.realpath

# and for folder hierarchies:
is_dir = os.path.isdir

# and for generic things:
exists = os.path.exists


# function templates for passing to log_and_run:
# (callable, shell_command)

def append(template, target):
    """write `template_content` to the end of the file at `target`.
    :param template: str path to content to write.
    :param target: str filename.
    :return None"""
    template_content = open(template).read()
    append_file = open(target, 'a')
    append_file.write("\n\n" + template_content)
    append_file.close()

append = (append, "echo $'\\n\\n' && cat %s >> %s")


def ensure_dir_path(name, mode=None):
    """If the path given does not exist, create it (as a directory), like
    `mkdir -p $@`.
    :param name: str *the path to be created*
    :param mode: int *the mode of ownership, default 0777*
    :return None"""
    kwargs = {}
    if mode is not None:
        kwargs['mode'] = mode
    try:
        os.makedirs(name, **kwargs)
    except OSError as mkdir_err:
        if not (mkdir_err.errno == errno.EEXIST and is_dir(args[0])):
            raise


ensure_dir_path = (ensure_dir_path, "mkdir -p %s")

create_symlink = (os.symlink, "ln -s %s %s")
remove_symlink = (os.unlink, "rm %s")
file_copy = (shutil.copyfile, "cp %s %s")


def walk(path):
    """Generator for iterating over a file tree from root directory at `path`.
    :param path: str *the path to walk*
    :return None"""
    for root, dirs, files in os.walk(path):
        for directory in dirs:
            yield os.path.join(root, directory)
        for leaf in files:
            yield os.path.join(root, leaf)


repository_path = None
create_path = None
append_path = None


def installed_path(repo_path):
    """Convert a path in the repo to the path it will be installed on.
    :param repo_path: str *path of file detected in the repo*
    :return the equivalent path after installation."""
    if create_path in repo_path:
        replace = create_path
    elif append_path in repo_path:
        replace = append_path
    else:
        raise fatal("invalid path %s" % repo_path)
    if replace[-1] != '/':
        replace += '/'
    return repo_path.replace(replace, '%s/.' % os.environ['HOME'])


def install_create(template, run_and_log):
    """install a path from the create/ directory
    :param template: str *path of the repository template*
    :param run_and_log: callable *function which logs and runs actions*
    return: None"""
    target = installed_path(template)

    # if the template is a folder:
    if is_dir(template):
        run_and_log(ensure_dir_path, target)
        return

    # for files, we check whether the target file already exists:
    if not exists(target):
        run_and_log(create_symlink, template, target)
        return

    # if it does, action depends on type:
    if is_symlink(target):
        if symlink_target(target) == template:
            # the file is already installed, nothing to do.
            return
        # we won't delete any data by removing it, so go ahead:
        warn("symlink at %s -> %s is being replaced by link to %s." % (
            target, symlink_target(target), template))
        run_and_log(remove_symlink, "rm %s", target)
        run_and_log(create_symlink, template, target)
        return

    if is_dir(target):
        # a directory exists which clashes with the file we want to create.
        # This is a fatal error.
        raise fatal("directory %s clashes with file to install %s." % (
            target, template))

    # target is an ordinary file: replacing will delete data. We compare the
    # contents of the template to the target. interpret content stanzas as
    # separated by two consecutive line feeds.
    target_content = open(target).read()
    template_content = open(template).read()
    template_stanzas = {
        s.strip() for s in template_content.split("\n\n") if s
    }

    # if identical, then there is no data lost in symlinking (and we have
    # the bonus that the file will catch new changes from the repo.)
    if target_content.strip() == template_content.strip():
        info("file at %s is identical to file to be installed, replacing with "
             "symlink." % target)
        run_and_log(remove_symlink, target)
        run_and_log(create_symlink, template, target)
        return

    # if the target is a subset of the template, we assume it is an old
    # version and also replace it.
    unknown_stanzas = {
        s.strip() for s in target_content.split("\n\n") if s
    } - template_stanzas

    if not unknown_stanzas:
        info("file at %s is a subset of the file to be installed, assuming "
             "safe and replacing with symlink." % target)
        run_and_log(remove_symlink, target)
        run_and_log(create_symlink, template, target)
        return

    # if it has any content that is not in the repo, warn the user to
    # manually merge and retry install.
    warn("file at %s has content not tracked in the repo. ignoring for now, "
         "manually merge in and retry installing." % target)


def install_append(template, run_and_log):
    """install a path from the append/ directory
    :param template: str *path of the repository template*
    :param run_and_log: callable *function which logs and runs actions*
    return: None"""
    target = installed_path(template)

    # if the template is a folder:
    if is_dir(template):
        run_and_log(ensure_dir_path, target)
        return

    # if it doesn't exist, create it:
    if not exists(target):
        info("append-target %s does not exist: creating it." % target)
        run_and_log(file_copy, template, target)
        return

    # only append the content if it isn't already there:
    target_content = open(target).read()
    target_stanzas = {s.strip() for s in target_content.split("\n\n") if s}
    template_content = open(template).read()
    template_stanzas = {
        s.strip() for s in template_content.split("\n\n") if s
    }

    if not target_stanzas & template_stanzas:
        # nothing from the template is present in the target:
        run_and_log(append, template, target)
        return

    if not template_stanzas - target_stanzas:
        # everything from the template is present in the target:
        info("file at %s already contains everything to be appended." %
             target)
        return

    warn("not appending to file %s as found a partial match with append "
         "content. Please clean up the existing file and retry installing." %
         target)


def install(dry_run=False):
    """perform actions to install these dotfiles, printing each action as we go.
    :param dry_run: bool *if True, only print. default False.*
    :return None"""
    def run_and_log(function, *arguments):
        """print a shell representation of an action, and optionally execute it.
        :param function: tuple of:
          python callable *the python function to execute.*
          format string *the shell template representation of `function`.*
        :param arguments: tuple(str) *arguments to `function`.*"""
        impl, shell_template = function
        print shell_template % arguments
        if not dry_run:
            impl(*arguments)

    for template in walk(create_path):
        install_create(template, run_and_log)

    # and the append stuff:
    for template in walk(append_path):
        install_append(template, run_and_log)


def uninstall(dry_run=False):
    """perform actions to uninstall these dotfiles, printing each action as we
    go.
    :param dry_run: bool *if True, only print. default False.*
    :return None"""
    # TODO
    pass


if __name__ == "__main__":
    repository_path = os.path.dirname(__file__)
    create_path = os.path.join(repository_path, 'create')
    append_path = os.path.join(repository_path, 'append')

    import sys
    args = sys.argv[1:]

    dr = '-p' in args
    action = args[-1]

    if action not in {'install', 'uninstall'}:
        sys.stderr.write("bad mode %s\n" % action)
        exit(1)

    locals()[action](dry_run=dr)
