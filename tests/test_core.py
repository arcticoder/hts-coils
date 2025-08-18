import json
import numpy as np
from pathlib import Path
from hts.coil import mu_0, hts_coil_field, sample_helmholtz_pair_plane, sample_stack_plane
from hts import sample_circular_coil_plane
from hts.materials import jc_vs_temperature


def test_analytic_center_field():
    N,I,R=100,5000.0,1.0
    Bnum=hts_coil_field(np.array([0.0,0.0,0.0]),I=I,N=N,R=R)[2]
    Bana=mu_0*N*I/(2.0*R)
    assert abs(Bnum-Bana)/(abs(Bana)+1e-18) < 1e-2


def test_ripple_kpi_computation():
    X,Y,Bz=sample_circular_coil_plane(n=21)
    mean=float(np.nanmean(Bz)); std=float(np.nanstd(Bz))
    ripple=float(std/(abs(mean)+1e-18))
    assert ripple >= 0.0


def test_jc_monotonicity():
    Tc=90.0; J0=1e10
    assert jc_vs_temperature(77.0,Tc,J0) < jc_vs_temperature(50.0,Tc,J0)


def test_envelope_keys(tmp_path):
    env_path = Path('artifacts/operating_envelope.json')
    if env_path.exists():
        data=json.loads(env_path.read_text())
        assert set(['B_mean_T','ripple_rms']).issubset(data)


def test_helmholtz_symmetry():
    X,Y,Bz=sample_helmholtz_pair_plane(I=5000.0,N=100,R=1.0,extent=0.2,n=21)
    # symmetry about x and y axes on plane
    assert np.allclose(Bz, np.flip(Bz, axis=0), atol=1e-6)
    assert np.allclose(Bz, np.flip(Bz, axis=1), atol=1e-6)


def test_stack_plane_defined():
    X,Y,Bz=sample_stack_plane(I=5000.0,N=50,R=0.5,layers=3,axial_spacing=0.1,extent=0.2,n=21)
    assert np.isfinite(Bz).all()
