from typing import Dict


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