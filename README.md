# Assistant to the Kernel Manager

Utility for working with [Jupyter](https://jupyter.org) kernelspecs.

![Assistant TO the Kernel Manager](http://i.imgur.com/F0WLaYR.jpg)


## Install

    gem install a2km


## Examples

    a2km clone python3 myenvpy3
    a2km set python3-copy display_name "Super cool Python Kernel"
    a2km add-env python3-copy SPARK_HOME=/path/to/spark
    a2km add-argv python3-copy -- --debug
    # <debug some stuff>
    a2km rm-argv python3-copy -- debug
