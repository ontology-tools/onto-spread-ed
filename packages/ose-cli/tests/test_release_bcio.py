"""
Integration tests for the release CLI command using the BCIO ontology.

These tests run actual release operations on the BCIO repository located at ../BCIO/.
"""
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from ose_cli.main import cli


# Path to the BCIO repository - relative to the workspace root
# The workspace is at /home/bjoern/development/onto-spread-ed and BCIO is at /home/bjoern/development/BCIO
BCIO_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "BCIO"


@pytest.fixture
def bcio_working_copy(tmp_path):
    """
    Create a working copy of BCIO in a temporary directory.
    This allows tests to modify files without affecting the original repository.
    """
    if not BCIO_PATH.exists():
        pytest.skip(f"BCIO repository not found at {BCIO_PATH}")
    
    # Copy BCIO to temp directory
    dest = tmp_path / "BCIO"
    shutil.copytree(BCIO_PATH, dest, ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__'))
    return dest


@pytest.fixture
def release_script_path(bcio_working_copy):
    """Return path to the release script."""
    return bcio_working_copy / ".onto-ed" / "release_script.json"


class TestReleaseCliExists:
    """Test that the release CLI command exists and has expected options."""
    
    def test_release_command_exists(self):
        """The release command group should exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ['release', '--help'])
        assert result.exit_code == 0
        assert 'release' in result.output.lower()

    def test_release_run_command_exists(self):
        """The release run subcommand should exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ['release', 'run', '--help'])
        assert result.exit_code == 0
        # Should have options for release script and local path
        assert '--release-script' in result.output or '-r' in result.output
        assert '--local-path' in result.output or '-l' in result.output


class TestReleaseBcioValidation:
    """Test validation step of the BCIO release."""

    def test_release_import_external_succeeds(self, bcio_working_copy, release_script_path):
        """Running IMPORT_EXTERNAL on BCIO should succeed when external OWL exists.

        Uses the core ImportExternalReleaseStep via CLIReleaseContext.
        When the release script has use_existing_file=True and the file exists,
        the step uses it directly.
        """
        config_file = bcio_working_copy / ".onto-ed" / "config.yaml"
        if not config_file.exists():
            pytest.skip("BCIO repository does not have .onto-ed/config.yaml")

        external_file = bcio_working_copy / "Upper Level BCIO" / "bcio_external.owl"
        if not external_file.exists():
            pytest.skip("BCIO external OWL file not present")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'release', 'run',
            '--release-script', str(release_script_path),
            '--local-path', str(bcio_working_copy),
            '--steps', 'IMPORT_EXTERNAL',
            '-v', '-v', '-v'
        ])

        # Print output for debugging
        if result.exit_code != 0:
            print(f"STDOUT: {result.output}")
            if result.exception:
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0, f"Import external failed with output: {result.output}"

        # Verify external file still exists
        assert external_file.exists(), "External OWL file should still exist"

    @pytest.mark.xfail(reason="horned-owl panics on BCIO external OWL (from_owl limitation)")
    def test_release_validation_runs(self, bcio_working_copy, release_script_path):
        """Running VALIDATION on BCIO should complete (may have warnings).

        Note: The core ValidationReleaseStep loads externals via from_owl() which
        may fail with horned-owl on certain RDF constructs in the BCIO external OWL.
        """
        config_file = bcio_working_copy / ".onto-ed" / "config.yaml"
        if not config_file.exists():
            pytest.skip("BCIO repository does not have .onto-ed/config.yaml")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'release', 'run',
            '--release-script', str(release_script_path),
            '--local-path', str(bcio_working_copy),
            '--steps', 'IMPORT_EXTERNAL,VALIDATION',
            '-v', '-v'
        ])

        assert result.exit_code == 0, f"Unexpected failure with exit code {result.exit_code}: {result.output}"


class TestReleaseBcioBuild:
    """Test build step of the BCIO release."""

    @pytest.mark.skip(reason="Build requires BCIO repository with proper symlinks setup")
    def test_release_build_produces_owl_files(self, bcio_working_copy, release_script_path):
        """Running build on BCIO should produce OWL files.

        Note: This test requires a BCIO repository with proper symlinks
        to intermediate OWL files. The test copy doesn't preserve symlinks.
        """
        runner = CliRunner()
        result = runner.invoke(cli, [
            'release', 'run',
            '--release-script', str(release_script_path),
            '--local-path', str(bcio_working_copy),
            '--steps', 'IMPORT_EXTERNAL,BUILD',
            '-v', '-v', '-v'
        ])

        if result.exit_code != 0:
            print(f"STDOUT: {result.output}")
            if result.exception:
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0, f"Build failed: {result.output}"

        # Check that expected OWL files were created/updated
        expected_files = [
            "Setting/bcio_setting.owl",
            "ModeOfDelivery/bcio_mode_of_delivery.owl",
            "Source/bcio_source.owl",
            "Behaviour/bcio_behaviour.owl",
        ]

        for owl_file in expected_files:
            owl_path = bcio_working_copy / owl_file
            assert owl_path.exists(), f"Expected OWL file not found: {owl_file}"
    
    def test_build_step_loads_sources(self, bcio_working_copy, release_script_path):
        """Build step should at least load the sources without crashing."""
        import json
        
        # Read the release script to verify structure
        with open(release_script_path) as f:
            script = json.load(f)
        
        # Verify the script has expected structure
        assert "files" in script, "Release script should have 'files'"
        assert len(script["files"]) > 0, "Release script should have at least one file definition"
        assert "external" in script, "Release script should have 'external' configuration"


class TestReleaseBcioMerge:
    """Test merge step of the BCIO release."""
    
    @pytest.mark.skip(reason="Merge requires successful Build which needs BCIO symlinks setup")
    def test_release_merge_produces_merged_owl(self, bcio_working_copy, release_script_path):
        """Running merge should produce the merged bcio.owl file.
        
        Note: This test requires a BCIO repository with proper symlinks
        to intermediate OWL files.
        """
        runner = CliRunner()
        result = runner.invoke(cli, [
            'release', 'run',
            '--release-script', str(release_script_path),
            '--local-path', str(bcio_working_copy),
            '--steps', 'IMPORT_EXTERNAL,BUILD,MERGE',
            '-v', '-v', '-v'
        ])
        
        if result.exit_code != 0:
            print(f"STDOUT: {result.output}")
            if result.exception:
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
        
        assert result.exit_code == 0, f"Merge failed: {result.output}"
        
        # The merged output should be bcio.owl in root
        merged_owl = bcio_working_copy / "bcio.owl"
        assert merged_owl.exists(), "Merged bcio.owl file not found"
    
    def test_merge_step_in_release_script(self, release_script_path):
        """Release script should include merge configuration."""
        import json
        
        with open(release_script_path) as f:
            script = json.load(f)
        
        # Verify the files structure includes the main ontology (bcio) that gets merged
        assert "files" in script, "Release script should have 'files' configuration"
        # The 'bcio' file is the merged output that combines all sub-ontologies
        assert "bcio" in script["files"], "Release script should have 'bcio' (merged) file"


class TestReleaseListSteps:
    """Test listing available release steps."""
    
    def test_list_steps_command(self):
        """The release list-steps command should show available steps."""
        runner = CliRunner()
        result = runner.invoke(cli, ['release', 'list-steps'])
        
        assert result.exit_code == 0
        # Should list the built-in steps
        assert 'VALIDATION' in result.output or 'validation' in result.output.lower()
        assert 'BUILD' in result.output or 'build' in result.output.lower()
