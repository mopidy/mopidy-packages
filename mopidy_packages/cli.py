import json
import pathlib
import shutil
import tempfile

import click

from mopidy_packages import models, web


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
@click.argument(
    'dest',
    default='_site',
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
        enrich_and_save(models.Person, build_path / 'people')
        enrich_and_save(models.Project, build_path / 'projects')

        shutil.rmtree(str(dest_path))
        build_path.replace(dest_path)
    finally:
        shutil.rmtree(str(build_path), ignore_errors=True)


def enrich_and_save(model, dest_path):
    if not dest_path.exists():
        dest_path.mkdir()

    label = 'Building %s objects:' % model.__name__.lower()

    with click.progressbar(list(model.all()), label=label) as objects:
        for obj in objects:
            try:
                obj.enrich()
            except Exception as exc:
                error_file = dest_path / ('%s.error' % obj.data['id'])
                with error_file.open('w') as fh:
                    fh.write(str(exc))
            else:
                json_file = dest_path / ('%s.json' % obj.data['id'])
                with json_file.open('w') as fh:
                    json.dump(obj.data, fh, indent=2)
