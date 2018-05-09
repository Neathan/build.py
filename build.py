# MIT License
# Copyright (c) 2018 Neathan
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json, argparse, hashlib, os, shutil, distutils.dir_util
from pathlib import Path
from subprocess import call

parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument("-c", "--clean", help="treat all files as changed", action="store_true")
parser.add_argument("-v", "--verbose", help="enter verbose mode", action="store_true")
parser.add_argument("-r", "--run", help="run the program after compilation", action="store_true")


# Parse the arguments
args = parser.parse_args()

# 
cfiles = []
newFiles = {}
data = {}
commands = []
filesChanged = False

# Load settings
if(Path("settings.json").exists()):
	with open("settings.json", encoding="utf-8") as settingsfile:
			settings = json.load(settingsfile)
else:
	print("No settings file found!")
	exit(2)

# Returns all sources files by filter
def getAllFilePaths(filter):
	pathlist = []
	for source in settings["SourceLocations"]:
		pathlist.extend(Path(source).glob(filter))
	return pathlist

# If the hashlibrary should be fully updated
haveFilesFile = Path("files.json").exists()
if(args.clean or not haveFilesFile):
	if(not haveFilesFile and args.verbose):
		print("No files file found forcing full update")

	# Remove all objects files
	shutil.rmtree(Path(settings["ObjectLocation"]));

	data["files"] = {}
	for extension in settings["FileSuffixes"]:
		pathlist = getAllFilePaths("**/*" + extension)
		for path in pathlist:
			str_path = str(path)
			cfiles.append(str_path)
			with open(str_path, "rb") as file:
				buf = file.read()
				hasher = hashlib.md5()
				hasher.update(buf)
				data["files"][str_path] = hasher.hexdigest()
	filesChanged = True

# If we should not fully update the hashlibrary
else:
	with open("files.json", encoding="utf-8") as file:
		data = json.load(file)
		files = data["files"]
	
	# Get what files has been updated and if any new files has been added
	for extension in settings["FileSuffixes"]:
		pathlist = getAllFilePaths("**/*" + extension)
		for path in pathlist:
			str_path = str(path)

			with open(str_path, "rb") as file:
				buf = file.read()
				hasher = hashlib.md5()
				hasher.update(buf)
				hash = hasher.hexdigest()

			if(str_path in files):
				if(files[str_path] != hash): # If the files hash i no longer the same, queue it for compilation
					cfiles.append(str_path)
					files[str_path] = hash
					filesChanged = True
			else: # New file found
				newFiles[str_path] = hash
				cfiles.append(str_path)
				filesChanged = True

	# Add new files
	data["files"].update(newFiles)

def generateCompileCommand(filePath):
	command = "clang++ -c "
	# If file is a in c add c compilation flag
	if(filePath.suffix == ".c"):
		command += "-x c" + " "
		# Add standard arguments
		for arg in settings["CStandardArguments"]:
			command += arg + " "
	else:
		# Add standard arguments
		for arg in settings["StandardArguments"]:
			command += arg + " "
	# Add source file
	command += str(filePath) + " "
	# Add header location
	for headerLocation in settings["HeaderLocations"]:
		command += "-I " + headerLocation + " "
	# Add output
	command += "-o " + str(Path(settings["ObjectLocation"] + filePath.name).with_suffix(".o"))
	return command

def generateLinkCommand():
	command = "clang++ "
	# Get all object files paths
	pathlist = Path(settings["ObjectLocation"]).glob("**/*.o")
	# Add object source files
	for path in pathlist:
		command += str(path) + " "
	# Add libraries
	for lib in settings["Libraries"]:
		command += lib + " "
	# Add library locaiton
	for libraryLocation in settings["LibraryLocations"]:
		command += "-L " + libraryLocation + " "
	# Add output
	command += "-o " + settings["OutputFile"] + settings["ExecutableSuffix"]
	return command

def generateLibraryLinkCommand():
	command = "ar -r "
	# Set output file
	command += settings["OutputFile"] + settings["LibrarySuffix"] + " "
	# Get all object files paths
	pathlist = Path(settings["ObjectLocation"]).glob("**/*.o")
	for path in pathlist:
		command += str(path) + " "
	return command


# Custom copytree function
def copytree_multi(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()
    if not os.path.isdir(dst):
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree_multi(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        except Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)


if(filesChanged == True):
	# If object location doesnt exis
	if(not Path(settings["ObjectLocation"]).exists()):
		os.makedirs(Path(settings["ObjectLocation"]))

	# Compile edited source files
	for file in cfiles:
		pfile = Path(file)
		if(pfile.suffix == ".h"):
			if(pfile.with_suffix(".cpp").exists()):
				file = str(pfile.with_suffix(".cpp"))
			elif(pfile.with_suffix(".c").exists()):
				file = str(pfile.with_suffix(".c"))
			else:
				continue
		command = generateCompileCommand(Path(file))
		if(command not in commands):
			if(args.verbose):
				print(command)
			error = os.system(command)
			if((error >> 8) != 0):
				print(command)
				if(not args.verbose):
					print("Error with shown command.")
				exit(1)
			else:
				commands.append(command)

	# Save files
	with open("files.json", "w") as output:
		json.dump(data, output, sort_keys=True, indent=4)

	if(settings["IsLibrary"] == True):
		linkCommand = generateLibraryLinkCommand()
		if(args.verbose):
			print(linkCommand)
		os.system(linkCommand)
		# Check if folder exists
		if(Path(settings["LibraryHeaderOutput"]).exists()):
			shutil.rmtree(Path(settings["LibraryHeaderOutput"]))
		# Move all headers
		ignore_func = lambda d, files: [f for f in files if (Path(d) / Path(f)).is_file() and not f.endswith('.h')]
		for source in settings["SourceLocations"]:
			copytree_multi(Path(source), Path(settings["LibraryHeaderOutput"]), ignore=ignore_func)
		for source in settings["HeaderLocations"]:
			copytree_multi(Path(source), Path(settings["LibraryHeaderOutput"]), ignore=ignore_func)

	else:
		# Link program
		linkCommand = generateLinkCommand()
		if(args.verbose):
			print(linkCommand)
		os.system(linkCommand)
else:
	if(args.verbose):
		print("No files changed")

# Run program
if(args.run):
	if(args.verbose):
		print("Running program")
	os.system("." + os.sep + settings["OutputFile"] + settings["ExecutableSuffix"])



# TODO
# 1: Should not be able to use -r when building a library
# 2: There might be problems with Path not automaticly resolving the absolute path