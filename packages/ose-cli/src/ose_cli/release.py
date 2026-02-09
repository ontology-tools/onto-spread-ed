from typing import Callable, Any, Dict, Tuple



def register_commands(cli):
    """Register release commands to the CLI (standalone Click)"""
    @cli.group("release")
    def release_group():
        """Commands for managing releases"""
        pass


def init_commands(cli, _: Callable[[Any], Callable[[Tuple[Any, ...], Dict[str, Any]], Any]]):
    """Initialize commands for Flask CLI (backward compatibility)"""
    
    @cli.group("release")
    def group():
        pass
