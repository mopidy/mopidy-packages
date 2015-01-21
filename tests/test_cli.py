import pathlib
from unittest import mock

import click.testing

import pytest

from mopidy_packages import cli


@pytest.fixture
def cli_runner():
    return click.testing.CliRunner()


def test_help(cli_runner):
    result = cli_runner.invoke(cli.cli, ['--help'])

    assert result.exit_code == 0
    assert result.output.startswith('Usage:')


def test_serve_ondemand_starts_web_server_with_defaults(cli_runner):
    with mock.patch.object(cli.web, 'app') as app_mock:
        result = cli_runner.invoke(cli.serve_ondemand, [])

        assert result.exit_code == 0
        app_mock.run.assert_called_once_with(
            port=5000, host='127.0.0.1', debug=False)


def test_serve_ondemand_starts_web_server_with_given_args(cli_runner):
    with mock.patch.object(cli.web, 'app') as app_mock:
        result = cli_runner.invoke(cli.serve_ondemand, [
            '--host', '0.0.0.0',
            '--port', '8000',
            '--debug',
        ])

        assert result.exit_code == 0
        app_mock.run.assert_called_once_with(
            port=8000, host='0.0.0.0', debug=True)


def test_serve_static_aborts_without_site_dir(cli_runner):
    with mock.patch.object(cli.web_static, 'app') as app_mock:
        with cli_runner.isolated_filesystem() as fs:
            result = cli_runner.invoke(cli.serve_static, [])

        assert result.exit_code == 1
        assert result.output == (
            'No site found at %s/_site. You must build it first.\n' % fs)
        assert app_mock.run.call_count == 0


def test_serve_static_starts_web_server_with_defaults(cli_runner):
    with mock.patch.object(cli.web_static, 'app') as app_mock:
        with cli_runner.isolated_filesystem() as fs:
            site_dir = pathlib.Path(fs) / '_site'
            site_dir.mkdir()
            result = cli_runner.invoke(cli.serve_static, [])

        assert result.exit_code == 0
        app_mock.run.assert_called_once_with(
            port=5000, host='127.0.0.1', debug=False)


def test_serve_static_starts_web_server_with_given_args(cli_runner):
    with mock.patch.object(cli.web_static, 'app') as app_mock:
        with cli_runner.isolated_filesystem() as fs:
            site_dir = pathlib.Path(fs) / '_site'
            site_dir.mkdir()
            result = cli_runner.invoke(cli.serve_static, [
                '--host', '0.0.0.0',
                '--port', '8000',
                '--debug',
            ])

        assert result.exit_code == 0
        app_mock.run.assert_called_once_with(
            port=8000, host='0.0.0.0', debug=True)


def test_build_static_freezes_api_site_to_disk(cli_runner):
    with mock.patch.object(cli.flask_frozen, 'Freezer') as freezer_class_mock:
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli.build_static, [])

        assert result.exit_code == 0
        freezer_class_mock.assert_called_once_with(cli.web.app)
        freezer_obj_mock = freezer_class_mock.return_value
        freezer_obj_mock.freeze.assert_called_once_with()


def test_build_static_cleans_dest_dir(cli_runner):
    with mock.patch.object(cli.flask_frozen, 'Freezer'):
        with cli_runner.isolated_filesystem() as fs:
            dest_path = pathlib.Path(fs) / 'dest'
            dest_path.mkdir()
            old_path = dest_path / 'old'
            old_path.mkdir()

            cli_runner.invoke(cli.build_static, ['dest'])

            assert not old_path.exists()
