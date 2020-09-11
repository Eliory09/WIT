import filecmp
import os
import random
from shutil import copy2
import time
from typing import Dict, List, Optional, Tuple


DIR_NAMES: Dict[str, str] = {"WIT": ".wit", "IMAGES": "images", "STAGING_AREA": "staging_area"}
COMMIT_ID_CHARS: str = "123456789abcdef"
COMMIT_ID_LENGTH: int = 40
COMMANDS: Dict[str, str] = {
    "INIT": "init",
    "ADD": "add",
    "COMMIT": "commit",
    "STATUS": "status",
    "REMOVE": "rm",
    "CHECKOUT": "checkout",
    "GRAPH": "graph",
    "BRANCH": "branch",
    "MERGE": "merge"
}
ERROR_MESSAGES: Dict[str, str] = {
    "INIT_USAGE": "Usage: python <path/to/wit.py> init",
    "ADD_USAGE": "Usage: python <path/to/wit.py> add <path>",
    "COMMIT_USAGE": "Usage: python <path/to/wit.py> commit <message>",
    "STATUS_USAGE": "Usage: python <path/to/wit.py> status",
    "REMOVE_USAGE": "Usage: python <path/to/wit.py> rm <path>",
    "CHECKOUT_USAGE": "Usage: python <path/to/wit.py> checkout <commit_id>",
    "GRAPH_USAGE": "Usage: python <path/to/wit.py> graph <--all (optional)>",
    "BRANCH_USAGE": "Usage: python <path/to/wit.py> branch <branch_name>",
    "MERGE_USAGE": "Usage: python <path/to/wit.py> merge <branch_name>"
}


def split_path(path: str) -> Tuple[str, Optional[str]]:
    """Split a path into the first parent directory containing a wit folder,
    and the relative path from it to file/directory received.
    Args:
        path (str): The path to split.
    Returns:
        tuple: The parent directory containing a wit folder, and the relative path from it.
    Example:
        WIT_DIRECTORY: home_dir/.wit
        WORKING DIRECTORY: home_dir/files
        path = "config.py"
        ---------
        Return value: (.../home_dir, files/config.py)
    """
    src: List[str] = []
    if os.path.isdir(DIR_NAMES["WIT"]):
        return path, None
    while path != '/':
        path, tail = os.path.split(path)
        src.append(tail)
        wit_folder: str = os.path.join(path, DIR_NAMES["WIT"])
        if os.path.isdir(wit_folder):
            src.reverse()
            src_path: str = "/".join(src)
            return path, src_path
    raise FileNotFoundError("No wit backup folder found. Create a backup using \"init\" command")


# Credits to Mateusz Kobos.
# https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi

def are_dir_trees_equal(dir1: str, dir2: str) -> bool:
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.
    Args:
        dir1 (str): First directory path
        dir2 (str): Second directory path
    Returns:
        bool: True if the directory trees are the same and 
              there were no errors while accessing the directories or files, 
              False otherwise.
    """
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        return False
    _, mismatch, errors = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


def create_meta_data(commit_id: str, images_dir: str, message: str, second_parent: Optional[str] = None) -> None:
    """Create meta data file (txt) for the current commit."""
    meta_data: Dict[str, str] = {"parent": "None", "date": "", "message": ""}
    references_path = os.path.join(images_dir, "references.txt")
    if os.path.isfile(references_path):
        if second_parent is None:
            meta_data["parent"] = get_head_commit_id(references_path)
        else:
            parents = ",".join([get_head_commit_id(references_path), second_parent])
            meta_data["parent"] = parents
    meta_data["date"], meta_data["message"] = time.ctime(), message
    with open(os.path.join(images_dir, f"{commit_id}.txt"), "w") as file:
        content = [f"{key}={value}\n" for key, value in meta_data.items()]
        file.writelines(content)
    
            
def create_image_dir(home_dir: str) -> str:
    """Create an image directory in .wit/images directory."""
    commit_chars: List[str] = random.choices(COMMIT_ID_CHARS, k=COMMIT_ID_LENGTH)
    commit_id: str = "".join(commit_chars)
    os.mkdir(os.path.join(home_dir, DIR_NAMES["WIT"], DIR_NAMES["IMAGES"], commit_id))
    return commit_id


def get_head_commit_id(references_path: str) -> str:
    """Return the head commit id."""
    with open(references_path, "r") as file:
        commit_id: str = file.read().splitlines()[0].split("=")[1]
    return commit_id


def get_master_commit_id(references_path: str) -> str:
    """Return the head commit id."""
    with open(references_path, "r") as file:
        commit_id: str = file.read().splitlines()[1].split("=")[1]
    return commit_id


def write_to_log(error: Exception) -> None:
    with open("wit_log.txt", "a") as file:
        file.write(f"{time.ctime()}: {error}")


def get_dirs_diffs(dir1: str, dir2: str, changes: List[str], by_content: bool = False) -> None:
    """Get directories differences.
    All different files are saved in 'changes' list.
    by_content - defines whether the check is determined by file names or by content (for common files).
    Args:
        dir1 (str): The first directory.
        dir2 (str): The second directory.
        changes (list of str): The differences between the folders.
        by_content (bool): Flag to determine the kind of check.
    Returns:
        None.
    """
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if by_content:
        changed_files = filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, False)[1]
        changes.extend([os.path.join(dir2, item) for item in changed_files])
    else:
        diff_files = dirs_cmp.right_only
        changes.extend([os.path.join(dir2, item) for item in diff_files])
    if not dirs_cmp.common_dirs:
        return
    for common_dir in dirs_cmp.common_dirs:
        new_dir1: str = os.path.join(dir1, common_dir)
        new_dir2: str = os.path.join(dir2, common_dir)
        if by_content:
            get_dirs_diffs(new_dir1, new_dir2, changes, by_content=True)
        else:
            get_dirs_diffs(new_dir1, new_dir2, changes)


def print_status(commit_id: Optional[str] = None, changes_to_commit: Optional[List[str]] = None, changes_not_staged: Optional[List[str]] = None, untracked_files: Optional[List[str]] = None) -> None:
    """Print the wit status."""
    if commit_id is None:
        print("No commit was found.")
        return
    print(f"Commit ID: {commit_id}")
    print(f"Changes to commit: {changes_to_commit}")
    print(f"Changes not staged for commit: {changes_not_staged}")
    print(f"Untracked files: {untracked_files}")


def get_branches(references_path: str) -> Dict[str, str]:
    """Get all branches and the commits they are pointing on.
    Args:
        references_path (str): The path to 'references.txt' file.
    Returns:
        branches (dict): All branches.
    """
    with open(references_path, "r") as file:
        content: List[str] = file.read().splitlines()[1:]
        branches: Dict[str, str] = {}
        for line in content:
            branch: str
            commit_id: str
            branch, commit_id = line.split("=")
            branches[branch] = commit_id
    return branches


def get_activated_branch(home_dir: str) -> str:
    """Get the activated branch
    Args:
        home_dir (str): The home directory of the project.
    Returns:
        branch (str): The activated branch.
    """
    activated_path: str = os.path.join(home_dir, DIR_NAMES["WIT"], "activated.txt")
    with open(activated_path, "r") as file:
        branch: str = file.read()
    return branch

            
def update_references(references_path: str, commit_id: str, branch: str = 'master') -> None:
    """Update references.txt file with the given parameters.
    Args:
        references_path (str): The 'references.txt' file path.
        commit_id (str): The HEAD commit.
        branch (str): The activated branch.
    Returns:
        None.
    """
    with open(references_path, 'r+') as file:
        content: List[str] = file.read().splitlines()
        params = {}
        for line in content:
            name, commit = line.split("=")
            params[name] = commit
        params["HEAD"] = commit_id
        if branch in params:
            params[branch] = commit_id
        content = [f"{key}={value}" for key, value in params.items()]
        file.seek(0)
        refs: str = "\n".join(content)
        file.write(refs)
        file.truncate()


def execute_checkout(src: str, dst: str, ignore: Optional[List[str]] = None) -> None:
    """Handles the checkout execution.
    Copy all files from src to dst recursively. Ignore the list of files given.
    Args:
        src (str): The source directory.
        dst (str): The destination directory.
        ignore (list of str): The files to ignore.
    Returns:
        None.
    """
    if ignore is None:
        ignore = []
    for item in os.listdir(src):
        s: str = os.path.join(src, item)
        d: str = os.path.join(dst, item)
        if os.path.isdir(s):
            execute_checkout(s, d, ignore)
        else:
            if item not in ignore:
                copy2(s, d)


def split_text_for_node(text: str) -> str:
    """Split a string to 10-chars length lines.
    Args:
        text (str): The string/text to split.
    Returns:
        str: The splitted text.
    """
    label_length: int = 10
    return "\n".join([text[j: j + label_length] for j in range(0, len(text), label_length)])


def get_all_commits(images_dir: str, commit_id: Optional[str] = None) -> List[str]:
    """Return all commits from HEAD.
    Args:
        images_dir (str): The images directory path.
        commit_id (str): The commit id to search from.
    Returns:
        commits (List[str]): All the commits made by the project's wit.
    """
    commits: List[str] = []
    references_path: str = os.path.join(images_dir, "references.txt")
    if commit_id is None:
        commit: str = get_head_commit_id(references_path)
    else:
        commit = commit_id
    get_all_commits_util(images_dir, commit, commits)
    return commits


def get_all_commits_util(images_dir: str, current_commit: str, commits: List[str]) -> None:
    """A recursive utility function for __get_all_commits_from_head."""
    parents: List[str] = get_parents(images_dir, current_commit)
    if not parents:
        commits.append(current_commit)
        return
    else:
        commits.append(current_commit)
        if len(parents) > 1:
            for parent in parents:
                get_all_commits_util(images_dir, parent, commits)
        else:
            get_all_commits_util(images_dir, parents[0], commits)


def get_parents(images_dir: str, commit_id: str) -> List[str]:
    """Get all parents of a commit."""
    meta_data_path: str = os.path.join(images_dir, (commit_id + ".txt"))
    with open(meta_data_path, "r") as file:
        parents = file.read().splitlines()[0].split("=")[1].split(",")
    if parents[0] == 'None':
        return []
    return parents


def merge_common_changes(common_file: str, branch_file: str, head_file: str, dst: str) -> None:
    """Merge common files that were edited by 2 users.
    Args:
        common_file (str): The common branch file (the original).
        branch_file (str): The same file edited in the branch passed to \'merge\' command.
        head_file (str): The same file edited in the head branch.
        dst (str): The destination path.
    Returns:
        None.
    """
    with open(common_file, "r") as file:
        common_content: List[str] = file.read().splitlines()
    with open(branch_file, "r") as file:
        branch_content: List[str] = file.read().splitlines()
    with open(head_file, "r") as file:
        head_content: List[str] = file.read().splitlines()
    
    merged_content: List[str] = []
    i: int = 0
    branch_len: int = len(branch_content)
    head_len: int = len(head_content)
    while i < branch_len or i < head_len:
        try:
            branch_line: str = branch_content[i]
        except IndexError:
            head_line: str = head_content[i]
            merged_content.append(head_line)
        else:
            try:
                head_line = head_content[i]
            except IndexError:
                merged_content.append(branch_line)
            else:
                common_line: str = common_content[i]
                if common_line != head_line and common_line != branch_line:
                    raise ValueError("Same row changed on both files. Aborting proccess.")
                elif common_line == head_line and common_line != branch_line:
                    merged_content.append(branch_line)
                else:
                    merged_content.append(head_line)
        i += 1

    with open(dst, "w") as file:
        file.write("\n".join(merged_content))

    
