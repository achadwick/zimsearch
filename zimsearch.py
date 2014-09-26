#!/usr/bin/python

import sys
import os
import dbus.service
import subprocess
from gi.repository import Gio, Gtk, GLib
from dbus.mainloop.glib import DBusGMainLoop

SEARCH_IFACE='org.gnome.Shell.SearchProvider2'


class ZimSearch(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="br.com.dsboger.zimsearch",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.service = ZimSearchService()
        
class ZimSearchService(dbus.service.Object):

    def __init__(self):
        name = dbus.service.BusName('br.com.dsboger.zimsearch.provider', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name=name, object_path='/br/com/dsboger/zimsearch/provider')
        self.notebook = None
        home = os.getenv('HOME', None)
        if not home:
            return None
        notebooks_list_file = os.getenv('XDG_CONFIG_HOME', home + "/.config") + "/zim/notebooks.list"
        for line in open(notebooks_list_file):
            index = line.find("Default=")
            if index == 0:
                self.notebook = line[8:].strip()
        self.timeout_id = None
        self.proc = None

    @dbus.service.method(dbus_interface=SEARCH_IFACE, 
                        in_signature='as', out_signature='as', 
                        async_callbacks=('reply_handler', 'error_handler'))
    def GetInitialResultSet(self, terms, reply_handler, error_handler):
        self.start_search(terms, reply_handler)
    
    @dbus.service.method(dbus_interface=SEARCH_IFACE, 
                        in_signature='asas', out_signature='as',
                        async_callbacks=('reply_handler', 'error_handler'))
    def GetSubsearchResultSet(self, prev_results, terms, reply_handler, error_handler):
        self.start_search(terms, reply_handler)
        
    def start_search(self, terms, reply_handler):
        search_notebook = None
        notebook_terms = []
        normal_terms = []
        for term in terms:
            index = term.find("notebook:")
            if index == 0:
                notebook_terms.append(term)
            else:
                normal_terms.append(term)
        terms = normal_terms
        if notebook_terms:
            search_notebook = notebook_terms[-1][9:].strip()
        if not search_notebook:
            search_notebook = self.notebook
        if not search_notebook:
            reply_handler([])
            return None

        if self.timeout_id or self.proc:
            self.cancel_search()
        query = " ".join(terms)
        args = ["/usr/bin/zim", "--search", search_notebook, query]
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        self.timeout_id = GLib.timeout_add(500, self.get_search_results, reply_handler, search_notebook)
        
    def get_search_results(self, reply_handler, search_notebook):
        if self.proc:
            (out, err) = self.proc.communicate()
            if out:
                identifiers = str(out, 'utf-8').split('\n')
                identifiers = [search_notebook + "#" + i for i in identifiers if len(i) > 0]
                reply_handler(identifiers)
            else:
                reply_handler([])
            self.proc = None
            self.timeout_id = None
        return False
        
    def cancel_search(self):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        if self.proc:
            self.proc.kill()
            self.proc = None
    
    @dbus.service.method(dbus_interface=SEARCH_IFACE, 
                        in_signature='as', out_signature='aa{sv}')
    def GetResultMetas(self, identifiers):
        metas = []
        for identifier in identifiers:
            parts = identifier.split("#")
            notebook = parts[0]
            page = parts[1]
            path = page.split(":")
            meta = {
                "id": identifier,
                "name": path[-1],
                "gicon": "text-x-generic",
                "description": "/".join(path[0:-1])
            }
            metas.append(meta)
        return metas
        
    @dbus.service.method(dbus_interface=SEARCH_IFACE, 
                        in_signature='sasu', out_signature='')
    def ActivateResult(self, identifier, terms, timestamp):
        parts = identifier.split("#")
        notebook = parts[0]
        page = parts[1]
        subprocess.call(["/usr/bin/zim", notebook, page])
    
    @dbus.service.method(dbus_interface=SEARCH_IFACE, 
                        in_signature='asu', out_signature='')
    def LaunchSearch(self, terms, timestamp):
        subprocess.call(["/usr/bin/zim"]) 


if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    app = ZimSearch()
    app.run(sys.argv)
