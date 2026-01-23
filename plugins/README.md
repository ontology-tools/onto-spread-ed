# Plugins for OntoSpreadEd

The functionality of OntoSpreadEd can be extended with plugins. To install a plugin place it in the configured plugin directory (`plugins` by default). Each plugin *MUST* be folder with at least a `plugin.py` in it which contains a single variable of type `ose.model.Plugin`. 

At the moment the following extensions are possible:

## Release step

A plugin may provide one or multiple release steps that can be used in the release configuration (release script) of repositories. A release step *MUST* sublcass and implement the abstract members of `ose.release.ReleaseStep`. Check the documentation of `run` functions and other helper functions in the class for further details.

## Script

A plugin may provide one or multiple scripts with parameters which are callable from the web front end. A script *MUST* be an instance of the `ose.model.Script` class. Scripts can perform arbitrary tasks as if they were part of the main application. Be careful and sanitize user input!

In addition to declared arguments, a script can request services via dependency injection by simply adding the argument with type annotation to the signature.
