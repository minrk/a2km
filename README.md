# Assistant to the Kernel Manager

Utility for working with [Jupyter](https://jupyter.org) kernelspecs.

## Install

```
pip install a2km
```

## Examples

```
a2km clone python3 python3-copy
a2km set python3-copy display_name "Super cool Python Kernel"
a2km add-env python3-copy SPARK_HOME=/path/to/spark
a2km add-argv python3-copy -- --debug
# <debug some stuff>
a2km rm-argv python3-copy -- debug
```

## Kernelspecs for environments

a2km has an `env-kernel` subcommand for creating kernelspecs for your conda or virtual environments.
Just pass a2km the name or path of the env, and you should be set:

```
conda create -n myenv ipykernel
a2km env-kernel myenv
python3 -m venv myvenv
a2km env-kernel myvenv --kind ./venv
```

## Commands

```
add-argv   Add argument(s) to a kernelspec launch command
add-env    Add environment variables to a kernelspec
clone      Clone a kernelspec
env-kernel Create a kernel from an env (conda or virtualenv)
help       Display global or [command] help documentation
locate     Print the path of a kernelspec
rename     Rename a kernelspec
rm         Remove a kernelspec
rm-argv    Remove arguments from a kernelspec launch command
rm-env     Remove environment variables from a kernelspec
set        Set a value in the kernelspec
show       Show info about a kernelspec
```

![Assistant TO the Kernel Manager](http://i.imgur.com/F0WLaYR.jpg)
