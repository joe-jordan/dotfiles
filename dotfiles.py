import os, os.path, errno, shutil

# alias some stdlib functions for manipulating symlinks:
is_symlink = os.path.islink
symlink_target = os.path.realpath

create_symlink = os.symlink
remove_symlink = os.unlink

# and for folder hierarchies:
is_dir = os.path.isdir

def ensure_dir_path(*args, **kwargs):
    try:
        os.makedirs(*args, **kwargs)
    except OSError as e:
        if not (e.errno == errno.EEXIST and is_path(args[0])):
            raise

# and for generic things:
exists = os.path.exists
file_copy = shutil.copyfile


def walk(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            yield os.path.join(root, d)
        for f in files:
            yield os.path.join(root, f)


repository_path = None
create_path = None
append_path = None


class InvalidPathError(Exception):
    pass


def installed_path(repo_path):
    if create_path in repo_path:
        replace = create_path
    elif append_path in repo_path:
        replace = append_path
    else: raise InvalidPathError
    if replace[-1] != '/':
        replace = replace + '/'
    return repo_path.replace(replace, '%s/.' % os.environ['HOME'])


def install(dry_run=False):
    """perform actions to install these dotfiles, printing each action as we go. dry_run=True => only print."""
    def do(function, fn_name, *arguments):
        print "%s %s" % (fn_name, " ".join(arguments))
        if not dry_run:
            function(*arguments)

    for template in walk(create_path):
        target = installed_path(template)

        # if the template is a folder:
        if is_dir(template):
            do(ensure_dir_path, "mkdir -p", target)
            continue

        # for files, we check whether the target file already exists:
        if not exists(target):
            do(create_symlink, "ln -s", template, target)
            continue

        # if it does, action depends on type:
        if is_symlink(target):
            if symlink_target(target) == template:
                # the file is already installed, nothing to do.
                continue
            # we won't delete any data by removing it, so go ahead:
            print "WARN: symlink at %s -> %s is being replaced by link to %s." % (target, symlink_target(target), template)
            do(remove_symlink, "rm", target)
            do(create_symlink, "ln -s", template, target)
            continue

        if is_dir(target):
            # a directory exists which clashes with the file we want to create. This is a fatal error.
            raise InvalidPathError("FATAL: directory %s clashes with file to install %s." % (target, template))

        # target is an ordinary file: replacing will delete data. We compare the contents of the template to the target.
        # interpret content stanzas as separated by two consecutive line feeds.
        target_content = open(target, 'r').read()
        template_content = open(template, 'r').read()
        template_stanzas = {s.strip() for s in template_content.split("\n\n") if s}

        # if identical, then there is no data lost in symlinking (and we have the bonus that the file will catch new
        # changes from the repo.)
        if target_content.strip() == tempalte_content.strip():
            print "WARN: file at %s is identical to file to be installed, replacing with symlink." % target
            do(os.unlink, "rm", target)
            do(create_symlink, "ln -s", template, target)
            continue

        # if the target is a subset of the template, we assume it is an old version and also replace it.
        unknown_stanzas = {s.strip() for s in target_content.split("\n\n") if s} - template_stanzas

        if not unknown_stanzas:
            print "WARN: file at %s is a subset of the file to be installed, assuming safe and replacing with symlink."
            do(os.unlink, "rm", target)
            do(create_symlink, "ln -s", template, target)
            continue

        # if it has any content that is not in the repo, warn the user to manually merge and retry install.
        print "WARN: file at %s has content not tracked in the repo. ignoring for now, manually merge in and retry installing."

    # aaand the append stuff:
    for template in walk(append_path):
        target = installed_path(template)

        # if the template is a folder:
        if is_dir(template):
            do(ensure_dir_path, "mkdir -p", target)
            continue

        # if it doesn't exist, create it:
        if not exists(target):
            print "WARN: append-target %s does not exist: creating it."
            do(file_copy, "cp", template, target)
            continue

        # only append the content if it isn't already there:
        target_content = open(target, 'r').read()
        target_stanzas = {s.strip() for s in target_content.split("\n\n") if s}
        template_content = open(template, 'r').read()
        template_stanzas = {s.strip() for s in template_content.split("\n\n") if s}

        if not (target_stanzas & template_stanzas):
            # nothing from the template is present in the target:
            def append():
                f = open(target, 'a')
                f.write("\n\n" + template_content)
                f.close()
            do(append, "echo $'\\n\\n' && cat %s >> %s" % (template, target))
            continue

        if not (template_stanzas - target_stanzas):
            # everything from the template is present in the target:
            print "INFO: file at %s already contains everything to be appended." % target
            continue

        print "WARN: not appending to file %s as found a partial match with append content. Please clean up the existing file and retry installing." % target


def uninstall(dry_run=False):
    """perform actions to uninstall these dotfiles, printing each action as we go. dry_run=True => only print."""
    # TODO
    pass

if __name__ == "__main__":
    repository_path = os.path.dirname(__file__)
    create_path = os.path.join(repository_path, 'create')
    append_path = os.path.join(repository_path, 'append')

    import sys
    args = sys.argv[1:]

    dry_run = '-p' in args
    mode = args[-1]

    if mode not in {'install', 'uninstall'}:
        sys.stderr.write("bad mode %s\n" % mode)
        os.exit(1)

    locals()[mode](dry_run=dry_run)
