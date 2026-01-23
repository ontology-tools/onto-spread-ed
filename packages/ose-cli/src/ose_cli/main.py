import click


@click.group()
def cli():
    """OntoSpreadEd CLI - Ontology spreadsheet editor command line interface"""
    pass


# Register command groups
from .externals import register_commands as register_externals
from .release import register_commands as register_release

register_externals(cli)
register_release(cli)


def main():
    cli()


if __name__ == "__main__":
    main()
