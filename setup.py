#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

from distutils.core import setup
from distutils.command.install_data import install_data
from distutils import log
import os
import sys
import textwrap


if not ((2,) < sys.version_info < (3,)):
    print("This program requires Python 2.x")
    print("Please re-run using 'python2 setup.py [...]'")
    sys.exit(1)


# Support classes:

class InstallDataSubst (install_data):
    """Standard install_data command, extended for variable substitution

    This recognises input filenames with ".in" filename extensions, and
    performs some variable subsitutions on them instead of a regular
    copy. Subst'ed output files are written without the extension.

    """
    # All this just because DBUS .service files require an absolute path

    def copy_file(self, infile, outfile, *args, **kwargs):
        if not infile.endswith(".in"):
            result = install_data.copy_file(self, infile, outfile,
                                            *args, **kwargs)
        else:
            out_basename = os.path.basename(infile)
            (out_basename, _) = os.path.splitext(out_basename)
            outfile = os.path.join(outfile, out_basename)
            log.info("expanding %s -> %s", infile, outfile)
            substs = [
                ("@INSTALLDIR@", self.install_dir),
            ]
            log.debug("substs: %r", substs)
            if not self.dry_run:
                in_fp = open(infile, 'r')
                if os.path.exists(outfile):
                    os.unlink(outfile)
                out_fp = open(outfile, 'w')
                for line in in_fp:
                    for s, r in substs:
                        line = line.replace(s, r)
                    out_fp.write(line)
                in_fp.close()
                out_fp.close()
            result = (outfile, 1)
        return result


# Script and GNOME search provider installation:

setup(
    name='zimsearch',
    version='0.0.0',
    description='GNOME integration for Zim',
    url='https://github.com/dsboger/zimsearch',
    requires=["dbus"],
    long_description=textwrap.dedent("""
        Integrates Zim into the GNOME search dialog.

        This plugin provides search results for GNOME Shell.
    """).strip(),
    author='Davi da Silva Böger',
    author_email='dsboger [at] gmail [dot] com',
    data_files=[
        ('share/zim/plugins',
            ["src/gnomeshellsearch.py"]),
        ('share/dbus-1/services',
            ["data/zim.plugins.gnomeshellsearch.provider.service.in"]),
        ('share/gnome-shell/search-providers',
            ["data/zim.plugins.gnomeshellsearch.provider.ini.in"]),
    ],
    cmdclass={'install_data': InstallDataSubst},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: Gnome",
        "Environment :: Plugins",
        ("License :: OSI Approved :: "
         "GNU General Public License v2 or later (GPLv2+)"),
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ]
)
