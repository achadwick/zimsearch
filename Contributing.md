# Contributing to Zimsearch

First of all, I'm super grateful to anyone who can help me maintain
Zimsearch. Thank you for taking the time to read this page, and for
considering helping out.

I'm happy to receive pull requests and issue reports against Zimsearch,
and I'll try to get things patched and fixed as time allows. This
document is for now a quick set of developer notes geared towards people
testing and debugging the Zimsearch code.

## Resources

* [Issue Tracker](https://github.com/achadwick/zimsearch/issues)
* [Installation Guide](INSTALL.md)
* [User Guide](README.md)

## Test and Debug

You can use the following command sequence to try out changes you make
to the code and to the installation.

1. Reinstall Zimsearch normally with `pip`,
   but don't log out and back in.

2. To run the fresh install in debug mode from your Terminal window,
   use the following:

    killall zim
    rm -fr "/tmp/zim-$USER"
    zim --plugin gnomeshellsearch --debug

3. Press <kbd>Meta</kbd> and type your search terms as normal.
   The Zim instace in your Terminal window will answer the queries as
   the you type via D-Bus.

4. Kill the instance of Zim running in your Terminal window with
   <kbd>Ctrl+C</kbd>.
