"""
src/generation — Resume generation pipeline with fabrication prevention.

Modules:
  context_builder.py     Layer 1: deterministic context assembly
  tier3_blocklist.py     Tier 3 tool blocklist (NEVER_CLAIM set)
  output_validator.py    Layer 3: post-generation fabrication detection

Entry point: context_builder.build_generation_context()
See: RESUME_GENERATION_PIPELINE_SPEC.md for full architecture.
"""
