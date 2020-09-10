from distutils.dir_util import copy_tree
import os
from shutil import copy2, rmtree
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from graphviz import Digraph  # type: ignore
from utilities import (are_dir_trees_equal, COMMANDS, create_image_dir, create_meta_data,
                       DIR_NAMES, ERROR_MESSAGES, execute_checkout, get_activated_branch, get_all_commits,
                       get_branches, get_dirs_diffs, get_head_commit_id, get_parents, print_status,
                       split_path, split_text_for_node, update_references, write_to_log)


def init() -> None:
    """Initialize a wit backup folder.
    Args:
        None.
    Returns:
        None.
    """
    home_dir: str = os.getcwd()
    try:
        os.mkdir(os.path.join(home_dir, DIR_NAMES["WIT"]))
        os.mkdir(os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"]))
        os.mkdir(os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"]))
    except OSError as e:
        write_to_log(e)
        print(e)
    else:
        with open(os.path.join(home_dir, DIR_NAMES["WIT"], "activated.txt"), 'w') as file:
            file.write("master")


def add(path: str) -> None:
    """Add a file or directory to the staging area folder.
    In case the wit backup folder is not in the working directory,
    the source file/directory will be copied to the staging area folder
    under the relative source path.
    Args:
        path (str): The file/directory to backup.
    Returns:
        None
    Example:
        WIT_DIRECTORY: home_dir/.wit
        WORKING DIRECTORY: home_dir/files/more_files
        >>> python path/to/wit.py add more_files
        Backup path: home_dir/.wit/files/more_files/ ... (all directory tree)
    """
    if not os.path.isdir(path) and not os.path.isfile(path):
        print(f"Error: No such file/directory as {path} exists")
        return None
    try:
        home_dir: str
        src: Optional[str]
        home_dir, src = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return None
    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    if src is None:
        dst: str = os.path.join(staging_dir, path)
    else:
        dst = os.path.join(staging_dir, src, path)
    if os.path.isfile(path):
        if os.path.isfile(dst):
            ans = input(f"The file {path} already exist in the staging area, would you like to copy it anyway (y/n)? ")
            while ans != 'y' and ans != 'n':
                ans = input(f"The file {path} already exist in the staging area, would you like to copy it anyway (y/n)? ")
            if ans == 'y':
                created_file: str = copy2(path, os.path.dirname(dst))
                print(f"The file {created_file} added to staging area.")
            else:
                print("Copy aborted by user.")
        else:
            created_file = copy2(path, os.path.dirname(dst))
            print(f"The file {created_file} added to staging area.")
    else:
        copy_tree(path, dst)
        print(f"The directory {dst} added to staging area.")


def commit(message: str, second_parent: Optional[str] = None) -> Optional[str]:
    """Commit a staging. Version is backed up in /"images" folder.
    Args:
        message (str): A message to save in the current version back-up.
    Returns:
        commit_id (str): The commit id.
    Example:
        WIT_DIRECTORY: home_dir/.wit
        >>> python <path/to/wit.py> commit <message>
        home_dir/.wit/staging_area ---- copy ---- > home_dir/.wit/images/commit_id
        (commit_id - 40 chars name generated randomly.)
    """
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return None

    # Define paths.
    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")

    # Check if the HEAD commit is equal to the current commit.
    # If so - abort the commit execution.
    if os.path.isfile(references_path):
        head_commit: str = get_head_commit_id(references_path)
        head_commit_dir: str = os.path.join(images_dir, head_commit)
        if are_dir_trees_equal(head_commit_dir, staging_dir):
            print("No changes made since the last commit. Commit aborted.")
            return None

    # Execute commit proccess.
    commit_id: str = create_image_dir(home_dir)
    create_meta_data(commit_id, images_dir, message, second_parent=second_parent)
    commit_dir: str = os.path.join(images_dir, commit_id)
    copy_tree(staging_dir, commit_dir)
    print(f"Commit executed. {commit_dir} created.")

    # Update "references.txt" file.
    activated_branch = get_activated_branch(home_dir)
    if os.path.isfile(references_path):
        update_references(references_path, commit_id, branch=activated_branch)
    else:
        with open(references_path, "w") as file:
            refs: str = "\n".join([f"HEAD={commit_id}", f"master={commit_id}"])
            file.write(refs)
    return commit_id


def remove(path: str) -> None:
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return
    
    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    target_path: str = os.path.join(staging_dir, path)
    if os.path.isfile(target_path):
        os.remove(target_path)
        print(f"{path} removed from the staging area.")
    elif os.path.isdir(target_path):
        ans: str = input("Would you like to remove the entire directory? (y/n)? ")
        while ans != 'y' and ans != 'n':
            ans = input("Would you like to remove the entire directory? (y/n)? ")
        if ans == 'y':
            rmtree(target_path)
            print(f"{path} removed from the staging area.")
        else:
            print("Deletion aborted by user.")
    else:
        print("No such file/directory found.")


def checkout(param: str) -> None:
    """Copy all commit files to the project's directory.
    Copy all commit files to the staging area. Change references accordingly (HEAD=commit_id).
    Args:
        param (str): The commit id/branch/\'master\' keyword.
    Returns:
        None.
    """
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return 
    
    # Get the project wit status.
    status_params = status(checkout=True)
    if status_params is None:
        print("Can not complete the checkout due to an unexpected error.")
        return
    changes_to_commit, changes_not_staged, untracked_files = status_params
    # Check if there are changes to commit or changes not staged.
    # If true, abort.
    if len(changes_to_commit) > 0 or len(changes_not_staged) > 0:
        print("Can not complete the checkout. Make sure all changes made to the project are fully committed.")
        return

    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")
    if not os.path.isfile(references_path):
        print("Can not complete the checkout. No commit found.")

    branches = get_branches(references_path)
    is_branch = False

    # If the commit is a branch - checkout its commit and activate it.
    if param in branches:
        commit_id = branches[param]
        is_branch = True
    else:
        commit_id = param

    commit_dir = os.path.join(images_dir, commit_id)
    # Copy the entire commit directory to the home directory.
    # Ignore the untracked files.
    try:
        execute_checkout(commit_dir, home_dir, ignore=untracked_files)
    except OSError as e:
        print("Copy proccess aborted due to an error.")
        write_to_log(e)
        print(e)
    else:
        # Copy the entire commit directory to the staging area.
        try:
            execute_checkout(commit_dir, staging_dir)
        except OSError as e:
            print("Copy to staging area proccess aborted due to an error.")
            write_to_log(e)
            print(e)
        else:
            # After all succeeded, update the references.
            if is_branch:
                update_references(references_path, commit_id=commit_id, branch=param)
                with open(os.path.join(home_dir, DIR_NAMES["WIT"], 'activated.txt'), "w") as file:
                    file.write(param)
            else:
                activated_branch = get_activated_branch(references_path)
                update_references(references_path, commit_id=commit_id, branch=activated_branch)
            print("Checkout proccess completed.")


def status(checkout: bool = False) -> Optional[Tuple[List[str], ...]]:
    """Print/return a status of the current project:
        - Files to be committed.
        - Changes not staged.
        - Untracked files (files not staged).
    Args:
        checkout (bool): If the status is for checkout operation,
                         the function will return the values instead of printing them.
    Returns:
        tuple: If checkout is True, return wit status. Else, returns None.
    """
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return None

    # Define paths.
    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")
    if not os.path.isfile(references_path):
        print_status()
        return None

    head_commit_id: str = get_head_commit_id(references_path)
    commit_dir: str = os.path.join(images_dir, head_commit_id)
    changes_to_commit: List[str] = []
    changes_not_staged: List[str] = []
    untracked_files: List[str] = []
    get_dirs_diffs(commit_dir, staging_dir, changes_to_commit)
    get_dirs_diffs(staging_dir, home_dir, changes_not_staged, by_content=True)
    get_dirs_diffs(staging_dir, home_dir, untracked_files)
    if checkout:
        return changes_to_commit, changes_not_staged, untracked_files
    else:
        print_status(head_commit_id, changes_to_commit, changes_not_staged, untracked_files)
        return None


def graph(all_commits: bool = False) -> None:
    """Build a graph showing hierarchy of wit commits,
    save it in the project's directory, and show it.
    Args:
        all_commits (bool): If True, all commits will be included on the graph. Otherwise, return False.
    Returns:
        None.
    """
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return

    # Define paths
    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")
    if not os.path.isfile(references_path):
        print("Can not complete the proccess. No commit found.")

    if not all_commits:
        commits = get_all_commits(images_dir)
    else:
        # All commits exist are directories which has .txt file with the same name.
        images: List[str] = list(filter(lambda x: x[-4:] == ".txt", os.listdir(images_dir)))
        commits = [image[:-4] for image in images
                   if os.path.isdir(os.path.join(images_dir, image[:-4]))]
    branches: Dict[str, str] = get_branches(references_path)
    head: str = get_head_commit_id(references_path)
    graph = Digraph(comment='.wiz commits', graph_attr={'rankdir': 'RL'})
    # Iterate through the commits, create a graph of commits and pointers.
    # The pointers are the branches. If there is a commit with a pointer on it - add it to the graph.
    i = 0
    while i < len(commits):
        label: str = split_text_for_node(commits[i])
        graph.node(name=commits[i], label=label, shape='circle', color='darkslategray3',
                   style='filled', fixedsize='True', width='2', height='2', fontsize='12')
        # Add a HEAD pointer.
        if commits[i] == head:
            graph.node(name='HEAD', label='HEAD', shape='plaintext', orientation='45')
            graph.edge('HEAD', head)
        # Add a branch (if points to the current commit).
        for branch, commit in branches.items():
            if commit == commits[i]:
                graph.node(name=branch, label=branch, shape='plaintext', orientation='45')
                graph.edge(branch, commit)
        # Connect all commits.
        parents = get_parents(images_dir, commits[i])
        for parent in parents:
            graph.edge(parent, commits[i], color='darkslategray3', style='filled')
        i += 1

    # Render and export.
    graph.render('graph', view=True, format='pdf')


def branch(name: str) -> None:
    """Create a new branch in the wit system.
    Args:
        name (str): The name/label of the branch.
    Returns:
        None.
    """
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return

    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")
    if not os.path.isfile(references_path):
        print("Can not complete the proccess. No commit found.")
        return
    
    with open(references_path, "a+") as file:
        end_of_file = file.tell()
        file.seek(0)
        content = file.read().splitlines()
        head_commit_id = content[0].split("=")[1]
        all_branches = [line.split("=")[0] for line in content]
        if name in all_branches:
            print(f"Branch name \'{name}\' is already in use. Aborting proccess.")
            return
        else:
            file.seek(end_of_file)
            file.write(f"\n{name}={head_commit_id}")


def merge(param: str) -> None:
    # Get the project home directory (parent of wit directory).
    try:
        home_dir: str
        home_dir, _ = split_path(os.getcwd())
    except FileNotFoundError as e:
        write_to_log(e)
        print(e)
        return
    
    staging_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["STAGING_AREA"])
    images_dir: str = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"])
    references_path: str = os.path.join(images_dir, "references.txt")
    if not os.path.isfile(references_path):
        print("Can not complete the proccess. No commit found.")
    
    branches = get_branches(references_path)
    if param in branches:
        src_commit_id = branches[param]
    else:
        src_commit_id = param
    try:
        src_commits: List[str] = get_all_commits(images_dir, commit_id=src_commit_id)
        head_commits: List[str] = get_all_commits(images_dir)
    except OSError as e:
        print("Wrong commit_id or branch name entered.")
        write_to_log(e)
        print(e)
        return
    common_commit = None
    for commit_id in src_commits:
        if commit_id in head_commits:
            common_commit = commit_id
    if common_commit is None:
        print("No common basis between the HEAD commit and the branch was found. Aborting.")
        return
    files_changed: List[str] = []
    get_dirs_diffs(os.path.join(images_dir, common_commit),
                   os.path.join(images_dir, src_commit_id),
                   files_changed)
    get_dirs_diffs(os.path.join(images_dir, common_commit),
                   os.path.join(images_dir, src_commit_id),
                   files_changed, by_content=True)
    src_image_dir = os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"], src_commit_id)
    print("Changed/added files merged to a new commit:")
    for item in files_changed:
        rel_dst = os.path.relpath(item, src_image_dir)
        print(rel_dst)
        copy2(item, os.path.join(staging_dir, rel_dst))
    new_commit_id = commit(f"Merge of {head_commits[0]} and {src_commit_id}", second_parent=src_commit_id)
    if new_commit_id is None:
        return
    else:
        activated_branch = get_activated_branch(home_dir)
        update_references(references_path, commit_id=new_commit_id, branch=activated_branch)


def run_command(command: Callable[..., Any], error_message: str, *args: Any, **kwargs: Any) -> None:
    """Run a wit command.
    Args:
        command (func): A function to run.
        error_message (str): An error message in case of failure.
        args (list): Positional arguments to pass. Optional.
        kwargs (dict): Keyword arguments to pass. Optional.
    """
    def no_args_command(command: Callable[[], Any]) -> None:
        """Handle no arguments command."""
        command()

    def args_command(command: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Handle command run with arguments."""
        if not kwargs:
            command(*args)
        elif not args:
            command(**kwargs)
        else:
            command(*args, **kwargs)

    try:
        if not args and not kwargs:
            no_args_command(command)
        else:
            args_command(command, *args, **kwargs)
    except TypeError as e:
        print(error_message)
        print(e)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == COMMANDS["INIT"]:
        run_command(init, ERROR_MESSAGES["INIT_USAGE"])
    elif args[0] == COMMANDS["ADD"]:
        run_command(add, ERROR_MESSAGES["ADD_USAGE"], *args[1:])
    elif args[0] == COMMANDS["COMMIT"]:
        run_command(commit, ERROR_MESSAGES["COMMIT_USAGE"], *args[1:])
    elif args[0] == COMMANDS["STATUS"]:
        run_command(status, ERROR_MESSAGES["STATUS_USAGE"])
    elif args[0] == COMMANDS["REMOVE"]:
        run_command(remove, ERROR_MESSAGES["REMOVE_USAGE"], *args[1:])
    elif args[0] == COMMANDS["CHECKOUT"]:
        run_command(checkout, ERROR_MESSAGES["CHECKOUT_USAGE"], *args[1:])
    elif args[0] == COMMANDS["GRAPH"]:
        if len(args) == 1:
            run_command(graph, ERROR_MESSAGES["GRAPH_USAGE"])
        elif len(args) == 2:
            if args[1] == '--all':
                run_command(graph, ERROR_MESSAGES["GRAPH_USAGE"], all_commits=True)
            else:
                print(ERROR_MESSAGES["GRAPH_USAGE"])
        else:
            print(ERROR_MESSAGES["GRAPH_USAGE"])
    elif args[0] == COMMANDS["BRANCH"]:
        run_command(branch, ERROR_MESSAGES["BRANCH_USAGE"], *args[1:])
    elif args[0] == COMMANDS["MERGE"]:
        run_command(merge, ERROR_MESSAGES["MERGE_USAGE"], *args[1:])
# Reupload 177