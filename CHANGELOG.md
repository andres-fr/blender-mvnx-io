# CHANGELOG
All notable changes to this project will be documented in this file.

* The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) where:
  - Versions adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`MAJOR.MINOR.PATCH`)
  - Dates are in `DD/MM/YYYY` format





## [[Unreleased](https://github.com/andres-fr/blender_mvnx_io/compare/0.1.0...HEAD)]

### Added

* Class for parsing MVNX into Mvnx object (Blender-agnostic)
* Importer operator with button in I/O panel
* Importer routine with mode for both connected and individual bones
* Import works with and without inheriting angles
* Importer allows resizing everything by a factor


### TODO:


* Compatibility with MakeHuman?
* CI with blender?
* Adapt skeleton depending on config like mvnx.subject.attrib["configuration"] = "UpperBody"
* Global rotation matrix?
* Is there a better handling of time scale/precision?
