# healer

    pip install -e data-layer/claim_graph   # dependency
    pip install -e data-layer/healer
    python -m healer.heal            # dry run
    python -m healer.heal --apply    # rewrite + audit (v3.claim_heals)

See SPEC.md. Created 2026-08-22 (plan B0) by moving `registers/heal.py` out of
a package whose SPEC forbids graph writes.
