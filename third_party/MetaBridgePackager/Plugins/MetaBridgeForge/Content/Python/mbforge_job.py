"""Commandlet entry for MetaBridge DNA's package jobs: mbforge_job.py <job.json>."""
import sys

from mbforge import mhpkg_job

mhpkg_job.run(sys.argv[-1])
