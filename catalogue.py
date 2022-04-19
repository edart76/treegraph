
from pathlib import Path
import importlib, importlib.util, importlib.machinery, \
        os, sys, pkgutil, inspect, pprint
import typing as T
from collections import namedtuple

from tree.lib.python import safeLoadModule
from tree import Signal
from treegraph.lib.python import iterSubClasses, iterSubModuleNames
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
	and gathering all valid classesToReload defined in them
	maybe a bit specific for a generic object but it's fine

	also defines logic for reloading individual known classesToReload
	"""
	# tuples of matching length holding old and new class objects,
	# and new module objects
	ReloadEvent = namedtuple("ReloadEvent", ("oldClasses",
	                                         "newClasses",
	                                         "modules"))
	RegisterEvent = namedtuple("RegisterEvent",("newClasses",
	                                            "newModules"))

	def __init__(self, classPackagePaths:T.List[T.Union[Path, str]], baseClasses=T.Set[type]):
		self.classModuleMap = {}
		self.scanPackagePaths = list(map(Path, classPackagePaths))
		self.scanBaseClasses = baseClasses
		self.classesChanged = Signal(name="classesRegistered")
		self.classesReloaded = Signal(name="classesReloaded")

		self.registerClasses(baseClasses)

	@property
	def classes(self)->T.Set[type]:
		"""return set of known classes"""
		return set(self.classModuleMap.keys())

	def gatherClasses(self):
		"""iterate over class package paths,
		gather valid subclasses, add them to class package map
		this naturally has to load all modules
		"""
		for path in self.scanPackagePaths:
			for rootPath, dirs, files in os.walk(path):
				# check if it's a valid python package
				if not "__init__.py" in files:
					continue
				rootPath = Path(rootPath)
				results = modulesInPackagePath(rootPath)

				# get members in modules
				for module in results:
					# # only unique members that are classesToReload
					# members = set(
					# 	[i[1] for i in inspect.getmembers(module, lambda x: isinstance(x, type))])
					# for testClass in members:
					# 	# skip invalid classesToReload
					# 	if not self.checkValidClass(testClass, module):
					# 		continue
					# 	self.classModuleMap[testClass] = module
					classes = self.getClassesInModule(module)
					for modClass in classes:
						self.classModuleMap[modClass] = module

	def getClassesInModule(self, module):
		classes = []
		# only unique members that are classesToReload
		members = set(
			[i[1] for i in inspect.getmembers(module, lambda x: isinstance(x, type))])
		for testClass in members:
			# skip invalid classesToReload
			if not self.checkValidClass(testClass, module):
				continue
			#self.classModuleMap[testClass] = module
			classes.append(testClass)
		return classes

	def checkValidClass(self, testClass:type, module):
		"""return True if testClass is to be included in catalogue,
		False if ignored
		tested working with dynamically-generated classesToReload at module-level
		"""
		# check that class is defined in module
		if inspect.getsourcefile(testClass) != module.__file__:
			return False
		return any(i in testClass.__mro__ for i in self.scanBaseClasses)

	def registerClasses(self, testClasses: T.Set[type]):
		"""register a given class directly - attempts to work out
		module from its source
		raises TypeError if class is not valid"""
		registeredClasses = []
		registeredModules = []
		for testClass in testClasses:
			modName = testClass.__module__
			sourceFile = inspect.getsourcefile(testClass)
			spec = importlib.util.spec_from_file_location(
				modName, sourceFile)
			mod = importlib.util.module_from_spec(spec)
			print("mod", mod)
			if not self.checkValidClass(testClass, mod):
				raise TypeError("Class {} is invalid to register in catalogue")

			self.classModuleMap[testClass] = mod
			registeredClasses.append(testClass)
			registeredModules.append(mod)
		# emit signal
		self.classesChanged(self.RegisterEvent(
			registeredClasses, registeredModules))

	def reloadClasses(self, classesToReload:T.List[type]):
		"""reload the modules holding a set of classesToReload, then reimport them
		this may lead to some classesToReload in catalogue being out of date,
		but accessing them via the catalogue means that is actually
		ok"""
		# check only known classesToReload are passed
		unknownClasses = set(classesToReload).difference(set(self.classModuleMap.keys()))
		if unknownClasses:
			raise RuntimeError("Tried to reload unknown classesToReload {}".format(unknownClasses))

		oldClasses = []
		newClasses = []
		newModules = []

		oldNewClassMap = {i : None for i in classesToReload}
		newClassModuleMap = {}
		#testClasses = set()
		# get modules to reload
		modulesToReload = set(self.classModuleMap[i] for i in classesToReload)
		for module in modulesToReload:
			newModule = importlib.reload(module)
			foundClasses = self.getClassesInModule(newModule)
			#testClasses.update(foundClasses)
			for foundClass in foundClasses:
				newClassModuleMap[foundClass] = module

		# pair up old class, new class and module
		validClasses = set(newClassModuleMap.keys())
		for oldClass in classesToReload:
			newClass = self.getMatchingReloadedClass(oldClass, validClasses)
			newModule = newClassModuleMap[newClass]
			oldClasses.append(oldClass)
			newClasses.append(newClass)
			newModules.append(newModule)

		event = self.ReloadEvent(oldClasses,
		                         newClasses,
		                         newModules)
		self.classesReloaded(event)


	def getMatchingReloadedClass(self, testClass:type, classPool:T.Set[type]):
		"""associated an old class with its reloaded version
		for now just check the class __name__ - don't go renaming
		classesToReload and them hot-reloading them."""
		for poolClass in classPool:
			if poolClass.__name__ == testClass.__name__:
				return poolClass
		return None




	def displayStr(self):
		return "{} : \n".format(self) + pprint.pformat(self.classModuleMap)

	def display(self):
		print(self.displayStr())



if __name__ == '__main__':
	cat = ClassCatalogue(classPackagePaths = ["F:/all_projects_desktop/common/edCode/treegraph/example"],
	baseClasses = {GraphNode}
)
	cat.gatherClasses()
	cat.registerClasses(GraphNode)
	cat.display()



