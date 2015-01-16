import pathlib
import shutil
import tempfile

import click

import flask_frozen

from mopidy_packages import web, web_static


@click.group()
def cli():
    """Tools for tracking projects in the Mopidy ecosystem."""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', default=False, help='Debug mode', is_flag=True)
def serve(host, port, debug):
    """Run web server with on-demand data fetching."""
    web.app.run(host=host, port=port, debug=debug)


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', default=False, help='Debug mode', is_flag=True)
@click.argument(
    'dest', default='_site',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
def serve_static(host, port, debug, dest):
    """Run web server with static data from `build` command."""

    web_static.app.config['SITE_DIR'] = dest
    web_static.app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument(
    'dest', default='_site',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
def build(dest):
    """Build static API site.

    Fetches updated API data and saves to the DEST directory.

    DEST will be deleted and replaced with updated data when the data fetch is
    complete.
    """
    dest_path = pathlib.Path(dest)
    click.echo('Destination dir: %s' % dest_path)

    build_dir = tempfile.mkdtemp()
    build_path = pathlib.Path(build_dir)

    try:
        web.app.config['FREEZER_DESTINATION'] = str(build_path)
        freezer = flask_frozen.Freezer(web.app)
        freezer.freeze()

        shutil.rmtree(str(dest_path))
        build_path.replace(dest_path)
    finally:
        shutil.rmtree(str(build_path), ignore_errors=True)
