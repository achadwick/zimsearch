# -*- coding: utf-8 -*-

# Copyright 2014 Davi da Silva Böger <dsboger@gmail.com>

'''Zim plugin to display Zim pages in GNOME Shell search results.
'''

import logging

logger = logging.getLogger('zim.plugins.gnomeshellsearch')


from zim.main import NotebookCommand

class GnomeShellSearchPluginCommand(NotebookCommand):
	'''Class to handle "zim --plugin GnomeShellSearch [NOTEBOOK]".'''
	
	arguments = ('[NOTEBOOK]',)

	def run(self):
		from zim.config import ConfigManager
		
		notebook, p = self.build_notebook()
		config_manager = ConfigManager()
		preferences = config_manager.get_config_dict('preferences.conf')['GnomeShellSearch']
		preferences.setdefault('search_all', True)
		Provider(notebook, preferences['search_all']).main()
		
from zim.plugins import PluginClass
		
class GnomeShellSearch(PluginClass):

	plugin_info = {
		'name': _('GNOME Shell Search'), # T: plugin name
		'description': _('''\
This plugin provides search results for GNOME Shell.

Disabling this plugin has no effect. Please, use the "System Settings > Search" to disable Zim search results.
'''), # T: plugin description
		'author': 'Davi da Silva Böger',
	}
	
	plugin_preferences = (
		('search_all', 'bool', _('Search all notebooks, instead of only the default'), True),
	)
	
	def __init__(self, config=None):
		PluginClass.__init__(self, config)


		
import dbus.service

SEARCH_IFACE='org.gnome.Shell.SearchProvider2'

class Provider(dbus.service.Object):

	def __init__(self, notebook=None, search_all=True):
		import dbus.mainloop.glib
		
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		name = dbus.service.BusName('net.launchpad.zim.plugins.gnomeshellsearch.provider', bus=dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name=name, object_path='/net/launchpad/zim/plugins/gnomeshellsearch/provider')
		
		self.notebook = notebook
		self.notebook_cache = {}
		self.timeout_id = None
		self.search_all = search_all
		
	def main(self):
		import gtk
		
		gtk.main()
		
	def quit(self):
		import gtk
		
		gtk.main_quit()

	@dbus.service.method(dbus_interface=SEARCH_IFACE, 
				in_signature='as', out_signature='as', 
				async_callbacks=('reply_handler', 'error_handler'))
	def GetInitialResultSet(self, terms, reply_handler, error_handler):
		self._start_search(terms, reply_handler)
	
	@dbus.service.method(dbus_interface=SEARCH_IFACE, 
				in_signature='asas', out_signature='as',
				async_callbacks=('reply_handler', 'error_handler'))
	def GetSubsearchResultSet(self, prev_results, terms, reply_handler, error_handler):
		self._start_search(terms, reply_handler)
		
	def _start_search(self, terms, reply_handler):
		notebook_terms = []
		normal_terms = []
		for term in terms:
			index = term.find("notebook:")
			if index == 0:
				notebook_terms.append(term[9:])
			else:
				normal_terms.append(term.lower())
		terms = normal_terms

		search_notebooks = self._get_search_notebooks(notebook_terms)
		if not search_notebooks:
			reply_handler([])
			return None

		if self.timeout_id:
			self._cancel_search()

		result = []
		for search_notebook in search_notebooks:
			for page in search_notebook.index.walk():
				page_name_lower = page.basename.lower()
				contains_all_terms = True
				for term in terms:
					if not term in page_name_lower:
						contains_all_terms = False
						break
				
				if contains_all_terms:
					result.append(search_notebook.name + "#" + page.name)

		reply_handler(result)
		
	def _get_search_results(self, reply_handler, search_notebook):
		pass
		
	def _cancel_search(self):
		pass
		
	def _get_search_notebooks(self, notebook_terms):
		import zim.notebook
		
		search_notebooks_info = []
		notebook_list = zim.notebook.get_notebook_list()
		if notebook_terms:
			for notebook_id in notebook_terms:
				notebook_info = notebook_list.get_by_name(notebook_id)
				if notebook_info:
					search_notebooks_info.append(notebook_info)
		elif self.search_all:
			search_notebooks_info.extend(notebook_list)
		else:
			search_notebooks_info.append(self.notebook.info)
			
		search_notebooks = []
		for notebook_info in search_notebooks_info:
			search_notebooks.append(self._load_notebook(notebook_info.name))
			
		return search_notebooks
		
	def _get_notebook(self, notebook_id=None):
		notebook = None
		if not notebook_id or notebook_id == self.notebook.name:
			notebook = self.notebook
		else:
			notebook = self._load_notebook(notebook_id)
		return notebook

	def _load_notebook(self, notebook_id):
		if notebook_id in self.notebook_cache:
			notebook = self.notebook_cache[notebook_id]
		else:
			import zim.notebook
				
			notebook_list = zim.notebook.get_notebook_list()
			notebook_info = notebook_list.get_by_name(notebook_id)
			if notebook_info:
				notebook, _ = zim.notebook.build_notebook(notebook_info)
				self.notebook_cache[notebook_id] = notebook
		return notebook
		
	@dbus.service.method(dbus_interface=SEARCH_IFACE, 
						in_signature='as', out_signature='aa{sv}')
	def GetResultMetas(self, identifiers):
		metas = []
		for identifier in identifiers:
			notebook_id, page_id = identifier.split("#")
			path = page_id.split(":")
			name = path[-1]
			description = "(%s) %s" % (notebook_id, "/".join(path[0:-1]))
			meta = {
				"id": identifier,
				"name": name,
				"gicon": "text-x-generic",
				"description": description
			}
			metas.append(meta)
		return metas
		
	def _get_server(self):
		import zim.ipc
		zim.ipc.start_server_if_not_running()
		return zim.ipc.ServerProxy()
	
	@dbus.service.method(dbus_interface=SEARCH_IFACE, 
						in_signature='sasu', out_signature='')
	def ActivateResult(self, identifier, terms, timestamp):
		notebook_id, page_id = identifier.split("#")
		server = self._get_server()
		search_notebook = self._get_notebook(notebook_id)
		gui = server.get_notebook(search_notebook)
		gui.present(page=page_id)
	
	@dbus.service.method(dbus_interface=SEARCH_IFACE, 
						in_signature='asu', out_signature='')
	def LaunchSearch(self, terms, timestamp):
		server = self._get_server()
		gui = server.get_notebook(self.notebook)
		gui.present()
		gui.open_page()
		
