### virtualenv-make-relocatable

Simple tool to make scripts provided by virtualenv relocatable
It's just the alternative for removed `virtualenv --relocatable`


#### Background

Historically virtualenv supported option `--relocatable` to rewrite shibangs for scripts installed in it. 
It's very useful option if you plan to create docker image from your virtualenv directory.
Unfortunately since version `20.0` virtualenv removed this option.

This project provides tool for performing removed functionality


#### How to use

just run `virtualenv-make-relocatable <VENV-DIRECTORY>` 
