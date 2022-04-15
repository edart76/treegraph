
import pkgutil, os, sys

from tree.lib.python import *


def itersubclasses(cls, _seen=None):
	"""
	itersubclasses(cls)
	http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
	Generator over all subclasses of a given class, in depth first order.
	"""

	if not isinstance(cls, type):
		raise TypeError('itersubclasses must be called with '
						'new-style classesToReload, not %.100r' % cls)
	if _seen is None: _seen = set()
	try:
		subs = cls.__subclasses__()
	except TypeError:  # fails only when cls is type
		subs = cls.__subclasses__(cls)
	for sub in subs:
		if sub not in _seen:
			_seen.add(sub)
			yield sub
			for sub in itersubclasses(sub, _seen):
				yield sub

def iterSubModuleNames(package=None, path=None, fullPath=True, debug=False):
	"""yields names of all modules in package - DOES NOT import them"""
	names = []
	if not path:
		path = package.__path__

		if debug: print("path {}".format(path))

	for loader, module_name, is_pkg in pkgutil.walk_packages(path):
		if debug: print("module name {}".format(module_name))
		names.append(module_name)
	if fullPath:
		names = [package.__name__ + "." + i for i in names]
	return names



