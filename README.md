# build.py
A c++ build system written in python

Usage:
```
build.py [-h] [-c] [-v] [-r]
```
Optional arguments:
```
-h, --help     show help message and exit
-c, --clean    treat all files as changed
-v, --verbose  enter verbose mode
-r, --run      run the program after compilation
```
Example settings file:
```json
{
	"StandardArguments": [
		"-std=c++17"
	],
	"CStandardArguments": [
	],
	"FileSuffixes": [
		".cpp",
		".h",
		".c"
	],
	"IsLibrary": true,
	"ObjectLocation": "obj/",
	"OutputFile": "app",
	"ExecutableSuffix": "",
	"LibrarySuffix": ".a",
	"LibraryHeaderOutput": "Include/",
	"SourceLocations": [
		"src/",
		"Libraries/Source/"
	],
	"LibraryLocations": [
		"Libraries/Linux/"
	],
	"HeaderLocations": [
		"Libraries/Include/"
	],
	"Libraries": [
		"-lglfw3",
		"-lGL",
		"-lGLU",
		"-ldl",
		"-lX11",
		"-lXi",
		"-lXrandr",
		"-lXxf86vm",
		"-lXinerama",
		"-lXcursor",
		"-pthread"
	]
}
```
