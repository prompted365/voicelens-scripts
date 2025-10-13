"""
VoiceLens Seeder - Synthetic Data Generation & Analytics for Voice AI Systems

A powerful CLI toolkit for generating realistic VCP 0.3 compliant conversation data,
computing perception gaps, and creating compelling GTM narratives for voice AI platforms.
"""

__version__ = "0.1.0"
__author__ = "Prompted LLC"
__email__ = "hello@prompted.com"

from .cli import main

__all__ = ["main"]