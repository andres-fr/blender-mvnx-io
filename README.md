# `io_anim_mvnx`


This repository hosts an addon for Input of MVNX MoCap data in Blender 2.80, as well as facilities to test, autodocument and package it.

## Installation:

As any other addon, simply add the `io_anim_mvnx` folder to any of Blender's `addon` locations, and activate it to get started.


----------------------------

# Info for developers:


### run all tests with coverage:

To be able to run the unit tests within blender, make sure both the module and its utest module are in blender's path (`ln -s <SOURCE> <LINK_PATH>` ). Check allowed paths from Blender with `import addon_utils; print(addon_utils.paths())`.


```
# with coverage:
blender -b --python ci_scripts/utest_with_coverage.py -- -n io_anim_mvnx -p 0.9
# without coverage:
blender -b --python io_anim_mvnx_utest/__init__.py
```


### Bump version:

Regular work is performed on the `dev` branch. After a milestone commit (and optional merge into `master`), tag it before pushing with:
```
bump2version {major | minor | patch}
```
And then a push will automatically trigger the tagged release.

### Build package:

```
python setup.py clean --all
rm -r *.egg-info
python setup.py sdist bdist_wheel
```


### Build docs:

Run this on repo root:

```
blender -b --python ci_scripts/make_sphinx_docs.py -- -n io_anim_mvnx -a "Andres FR" -f .bumpversion.cfg -o docs -l
```


### Branching:

Travis builds get triggered on `master` and tagged builds only. Regular work can be done on a `dev` branch:

```
# create branch right after a commit:
git checkout -b dev
# work normally on it...
...
# track the new branch if you want to implicitly push to it:
git push -u origin dev # the first time, then `git push`

# once a milestone is reached, merge into master:
xx
```


### Travis CI:

TODO (Have travis install Blender2.80 etc).
