## HTS Coil Prototype Experimental Validation Plan

### Testing Protocols

#### 1. Field Mapping and Validation
- **Hall probe field mapping**: 3D field measurement using calibrated Hall sensors
  - Grid resolution: 1cm spacing over central 20cm × 20cm × 10cm volume  
  - Accuracy target: ±0.1% field measurement
  - Compare with Biot-Savart predictions
  - Measure field ripple and uniformity

- **NMR field measurement**: High-precision field measurement at select points
  - Validate absolute field strength to ±0.01%
  - Check field stability over time (drift < 10 ppm/hour)

#### 2. Quench Detection and Protection
- **Voltage tap monitoring**: Install voltage taps every 10 turns
  - Detect resistive transitions > 1 μV threshold
  - Measure normal zone propagation velocity
  - Test quench protection system response time < 100 ms

- **Temperature monitoring**: Cernox sensors at critical locations
  - Monitor hot spot development during quench events
  - Validate thermal modeling predictions

#### 3. Thermal Cycling and Stability
- **Thermal cycling tests**: 300K → 20K → 300K cycles
  - Minimum 10 cycles to test mechanical stability
  - Monitor Ic degradation (target < 5% after 10 cycles)
  - Check for delamination or conductor damage

- **Operating stability**: Long-term field stability tests
  - Maintain field for 24+ hours at rated current
  - Monitor thermal stability and field drift

#### 4. Mechanical Validation
- **Strain gauge measurements**: Monitor hoop and radial strain
  - Compare with stress analysis predictions
  - Validate delamination margins during energization
  
- **Vibration testing**: Assess mechanical resonances
  - Avoid resonant frequencies during operation

### Cost and Timeline Estimates

#### Prototype Specifications (20% Scale)
- **Coil dimensions**: R = 0.2m, N = 400 turns per coil
- **REBCO tape**: 20.1 km total (±10% procurement uncertainty)  
- **Estimated costs** (±20% uncertainty):
  - REBCO tape: $402,000 ± $80,000
  - Cryogenic system: $150,000 ± $30,000
  - Mechanical support: $75,000 ± $15,000
  - Instrumentation: $50,000 ± $10,000
  - **Total**: $677,000 ± $135,000

#### Build Timeline (±4 weeks uncertainty)
1. **Design finalization**: 4 weeks ± 1 week
2. **REBCO tape procurement**: 12 weeks ± 2 weeks  
3. **Mechanical fabrication**: 8 weeks ± 2 weeks
4. **Coil winding and assembly**: 6 weeks ± 1 week
5. **System integration and testing**: 4 weeks ± 1 week
6. **Experimental validation**: 6 weeks ± 2 weeks
   **Total duration**: 40 weeks ± 9 weeks

### Collaboration and Outreach

#### Target Laboratories
- **Fermilab**: Superconducting magnet expertise, test facilities
- **CERN**: Antimatter research collaboration, validation with ALPHA/AEgIS teams
- **MIT/CFS**: Fusion magnet experience, REBCO tape characterization
- **NHMFL**: High-field magnet testing, infrastructure access

#### Collaboration Benefits  
- Access to specialized test equipment (high-current power supplies, field mapping robots)
- Validation against established magnetic confinement systems
- Potential for joint publications and follow-on research
- Shared cost reduction through facility access agreements

### Risk Mitigation
- **Technical risks**: Parallel testing at multiple scales (10%, 20%, 50%)
- **Cost overruns**: Modular design allowing phased construction
- **Timeline delays**: Overlap activities where possible, maintain buffer time
- **Performance shortfalls**: Conservative design margins, fallback configurations

### Success Criteria
- **Field performance**: Achieve >90% of predicted field strength
- **Uniformity**: Demonstrate <1% ripple in central confinement volume  
- **Thermal stability**: Operate continuously for >24 hours without quench
- **Mechanical integrity**: No degradation after 10 thermal cycles
- **Cost validation**: Stay within ±25% of estimated prototype cost

This experimental plan provides comprehensive validation while maintaining realistic resource requirements and timeline expectations.