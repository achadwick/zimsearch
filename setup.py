#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

from __future__ import print_function

import os
import sys
import textwrap


# The launcher script doesn't strictly require Python 2, but the plugin
# code does. Not that we install any modules just yet.

if not ((2,) < sys.version_info < (3,)):
    print("This program requires Python 2.", file=sys.stderr)
    print("Please re-run with python2 (or pip2).", file=sys.stderr)
    sys.exit(1)


# Setuptools/distutils import compatability:

try:
    from setuptools import setup
    from setuptools.command.install import install as _install
    USING_SETUPTOOLS = True
except:
    print("WARNING: Failed to import setuptools.", file=sys.stderr)
    print("Falling back to distutils.", file=sys.stderr)
    print("NOTE: Using 'pip' is *not* supported in this configuration.",
          file=sys.stderr)
    from distutils.core import setup
    from distutils.command.install import install as _install
    USING_SETUPTOOLS = False
finally:
    from distutils.command.install_data import install_data as _install_data


# Support classes:

class install (_install):  # noqa: N801
    """Standard install command, extended for data & var substitution.

    Setuptools has a design flaw whereby data cannot be installed except
    as package data. Since everything about this double-ended plugin is
    a data file, that's a problem. We want setuptools for its support
    of "pip uninstall" however, because the alternatives are nasty.

    """

    def run(self):
        """Override, adding back in what "install_data" used to do."""
        _install.run(self)

        if USING_SETUPTOOLS:
            install_data = self.get_finalized_command("install_data")
            install_data.run()


class install_data (_install_data):  # noqa: N801
    """Standard install_data command, extended for variable substitution

    This recognises input filenames with ".in" filename extensions, and
    performs some variable subsitutions on them instead of a regular
    copy. Subst'ed output files are written without the extension.

    """
    # All this just because DBUS .service files require an absolute path

    @property
    def substs(self):
        try:
            return self.__substs
        except AttributeError:
            install_scripts = self.get_finalized_command("install_scripts")
            self.__substs = [
                ("@INSTALL_DATA_DIR@", self.install_dir),
                ("@INSTALL_SCRIPTS_DIR@", install_scripts.install_dir),
            ]
            return self.__substs

    def copy_file(self, infile, outdir, *args, **kwargs):
        """Copy a file into place, with substitutions.

        The destination must be a directory, not a file.

        """
        if not infile.endswith(".in"):
            result = _install_data.copy_file(self, infile, outdir,
                                             *args, **kwargs)
        else:
            out_basename = os.path.basename(infile)
            (out_basename, _) = os.path.splitext(out_basename)
            outfile = os.path.join(outdir, out_basename)
            self.announce("expanding %s -> %s" % (infile, outfile),
                          level=2)
            self.announce("substs: %r" % (self.substs,), level=1)
            if not self.dry_run:
                in_fp = open(infile, 'r')
                if os.path.exists(outfile):
                    os.unlink(outfile)
                out_fp = open(outfile, 'w')
                for line in in_fp:
                    for s, r in self.substs:
                        line = line.replace(s, r)
                    out_fp.write(line)
                in_fp.close()
                out_fp.close()
            result = (outfile, 1)
        return result

    def run(self):
        """Override for the default, with more permissions management."""

        # Assume this bit gets mkpath() permissions right.
        _install_data.run(self)

        # Make sure that every data file that got installed is at least
        # world-readable.
        if not self.dry_run:
            rrr = 0o444
            for file in self.outfiles:
                sbuf = os.stat(file)
                assert sbuf is not None, "Installation has not taken place"
                if (sbuf.st_mode & rrr) != rrr:
                    mode = sbuf.st_mode | rrr
                    self.announce(
                        "chmod 0%03o %r" % (mode & 0o666, file),
                        level=2,
                    )
                    os.chmod(file, mode)


# Script and GNOME search provider installation:

setup(
    name='zimsearch',
    version='0.0.2a',  # SemVer, interfaces unstable [0.x] while Zim's are too.
    license="GPL-2.0+",
    description='GNOME integration for Zim 0.67+',
    url='https://github.com/achadwick/zimsearch',
    requires=["dbus"],
    long_description=textwrap.dedent("""
        Integrates Zim into the GNOME search dialog.

        This plugin provides search results from Zim in GNOME-shell's
        desktop search overlay.
    """).strip(),
    author='Andrew Chadwick',  # Formerly Davi da Silva Böger (@dsboger)
    author_email='a.t.chadwick@gmail.com',
    scripts=["zim-gnomeshellsearch"],
    data_files=[
        ('share/zim/plugins',
            ["src/gnomeshellsearch.py"]),
        ('share/dbus-1/services',
            ["data/zim.plugins.gnomeshellsearch.provider.service.in"]),
        ('share/gnome-shell/search-providers',
            ["data/zim.plugins.gnomeshellsearch.provider.ini.in"]),
    ],
    cmdclass={
        'install': install,
        'install_data': install_data,
    },
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
    ],
    include_package_data=True,
)
