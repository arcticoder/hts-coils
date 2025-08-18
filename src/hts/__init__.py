"""HTS coil modeling utilities (HTS-only focus: B, ripple, efficiency, thermal margin)."""
try:
    from .coil import hts_coil_field, sample_circular_coil_plane  # type: ignore
except Exception:  # pragma: no cover
    def hts_coil_field(*args, **kwargs):  # type: ignore
        raise RuntimeError("hts.coil.hts_coil_field unavailable")
    def sample_circular_coil_plane(*args, **kwargs):  # type: ignore
        raise RuntimeError("hts.coil.sample_circular_coil_plane unavailable")
__all__ = ["hts_coil_field", "sample_circular_coil_plane"]
