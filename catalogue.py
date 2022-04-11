
from pathlib import Path
import importlib, importlib.util, importlib.machinery, \
        os, sys, pkgutil, inspect, pprint
import typing as T

from tree.lib.python import safeLoadModule
from tree import Signal
from treegraph.lib.python import itersubclasses, iterSubModuleNames
from treegraph.node import GraphNode


def modulesInPackagePath(packagePath, includeParent=True,
                         loadModules=True):
	"""if not loadModules, returns loader objects
	else returns full loaded modules"""
	rootPath = Path(packagePath)
	results = []

	# don't worry about package alias now
	packageName = ".".join(rootPath.parts[2:])
	spec = importlib.util.spec_from_file_location(
		packageName, rootPath / "__init__.py")
	parentLoader = spec.loader
	results.append(parentLoader)
	for importer, packageName, isPkg in \
			pkgutil.iter_modules([str(rootPath)]):
		importer: importlib.machinery.FileFinder

		loader = importer.find_module(packageName)
		results.append(loader)

	if not includeParent:
		results = results[1:]
	if loadModules:
		results = [i.load_module() for i in results]
	return results


class ClassCatalogue(object):
	"""object with logic for iterating over a set of packages
	and gathering all valid classes defined in them
	maybe a bit specific for a generic object but it's fine

	also defines logic for reloading individual known classes
	"""


	def __init__(self, classPackagePaths:T.List[T.Union[Path, str]], baseClasses=T.Set[type]):
		self.classModuleMap = {}
		self.classPackagePaths = list(map(Path, classPackagePaths))
		self.baseClasses = baseClasses

	def gatherClasses(self):
		"""iterate over class package paths,
		gather valid subclasses, add them to class package map
		this naturally has to load all modules
		"""
		for path in self.classPackagePaths:
			for rootPath, dirs, files in os.walk(path):
				# check if it's a valid python package
				if not "__init__.py" in files:
					continue
				rootPath = Path(rootPath)
				results = modulesInPackagePath(rootPath)

				# get members in modules
				for module in results:
					# only unique members that are classes
					members = set(
						[i[1] for i in inspect.getmembers(module, lambda x: isinstance(x, type))])
					for testClass in members:
						# skip invalid classes
						if not self.checkValidClass(testClass, module):
							continue
						self.classModuleMap[testClass] = module

	def checkValidClass(self, testClass:type, module):
		"""return True if testClass is to be included in catalogue,
		False if ignored
		tested working with dynamically-generated classes at module-level
		"""
		# check that class is defined in module
		if inspect.getsourcefile(testClass) != module.__file__:
			return False
		return any(i in testClass.__mro__ for i in self.baseClasses)

	def registerClass(self, testClass: type):
		"""register a given class directly - attempts to work out
		module from its source
		raises TypeError if class is not valid"""
		modName = testClass.__module__
		sourceFile = inspect.getsourcefile(testClass)
		spec = importlib.util.spec_from_file_location(
			modName, sourceFile)
		mod = importlib.util.module_from_spec(spec)
		print("mod", mod)
		if not self.checkValidClass(testClass, mod):
			raise TypeError("Class {} is invalid to register in catalogue")

		self.classModuleMap[testClass] = mod
		#self.display()

	def displayStr(self):
		return "{} : \n".format(self) + pprint.pformat(self.classModuleMap)

	def display(self):
		print(self.displayStr())

	def reloadClasses(self, classes:T.List[type]):
		"""reload the modules holding a set of classes, then reimport them
		this may lead to some classes in catalogue being out of date,
		but accessing them via the catalogue means that is actually
		ok"""


if __name__ == '__main__':
	cat = ClassCatalogue(classPackagePaths = ["F:/all_projects_desktop/common/edCode/treegraph/example"],
	baseClasses = {GraphNode}
)
	cat.gatherClasses()
	cat.registerClass(GraphNode)
	cat.display()



