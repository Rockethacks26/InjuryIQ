#!/usr/bin/env python3
"""Test Gemini injury analysis - suppresses warnings so response is visible."""
import os
import sys
import warnings

warnings.filterwarnings("ignore")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from ai_analysis import analyze_injury_risk

r = analyze_injury_risk(120, 170, minutes_played=87)
print("Gemini response:", r)
