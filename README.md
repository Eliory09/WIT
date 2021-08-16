# WIT

WIT is a basic version control system (VCS) for local use.
Made as a project for [Python Free Course](https://github.com/PythonFreeCourse/Notebooks).

### Installation

WIT requires [Python](https://graphviz.readthedocs.io/en/stable/) and [Graphviz](https://graphviz.readthedocs.io/en/stable/) to fully operate.

To install the library simply clone it to a separate directory of your choice and run it from CMD/terminal.

```sh
$ git clone https://github.com/Eliory09/WIT
$ python3 <path/to/wit.py> <command> <args>
```

### Commands

| Command | Description |
| ------ | ------ |
| init | Sets up a new WIT local repository.|
| add <path> | Adds a new file/directory to the staging area. |
| commit | Commit the local changes added to the staging area. |
| status | Status on the WIT staging. |
| checkout <commit_id/branch> | Copy the commit files to the working tree. |
| graph <--all> | Export a view a graph containing WIT commits and branches. |
| branch <name> | Creates a branch from the HEAD-attached commit. |
| merge <commit_id/branch> | Merge files from current HEAD commit and passed commit to a new commit. |


### Contributors
Thanks to Yam Mesika for guiding me through the coding process.
