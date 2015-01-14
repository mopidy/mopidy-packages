import click

from mopidy_packages import web


@click.group()
def cli():
    """Tools for tracking projects in the Mopidy ecosystem."""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', default=False, help='Debug mode', is_flag=True)
def serve(host, port, debug):
    """Run web server which fetches data as needed."""
    web.app.run(host=host, port=port, debug=debug)
