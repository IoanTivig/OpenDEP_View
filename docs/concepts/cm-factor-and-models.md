# CM factor and models

## Dielectrophoresis and the CM factor

In a non-uniform AC field a polarisable particle feels the DEP force

F<sub>DEP</sub> = 2π ε<sub>m</sub> r³ Re[K(f)] ∇E²

with ε<sub>m</sub> the permittivity of the medium, r the particle radius, ∇E² the gradient of the squared field and **K(f)** the **Clausius-Mossotti (CM) factor**

K(f) = (ε<sub>p</sub>* − ε<sub>m</sub>*) / (ε<sub>p</sub>* + 2 ε<sub>m</sub>*),  ε* = ε − i σ / (2π f)

where ε<sub>p</sub>* and ε<sub>m</sub>* are the complex permittivities of particle and medium. Re[K] lies between −0.5 and 1:

- **Re[K] > 0: positive DEP (pDEP)**: the particle moves to the strong field (electrode edges).
- **Re[K] < 0: negative DEP (nDEP)**: it moves away, to the weak field.
- **Re[K] = 0: crossover**: no net force. The frequency where this happens is the **crossover frequency**.

A DEP spectrum is Re[K] measured over frequency. Its shape reflects the cell's dielectric properties: the first crossover mostly the membrane capacitance and the cell size, the high-frequency plateau the cytoplasm.

## Shell models

A cell is not a uniform particle: it is a conducting interior wrapped in a thin insulating membrane (and sometimes a wall, a nucleus). Shell models replace each layer, from the inside out, by an equivalent homogeneous sphere, until the whole cell is one particle with an effective complex permittivity ε<sub>p</sub>*:

| Model | Layers (inside → out) | Typical for |
|---|---|---|
| Homogeneous | particle | beads, liposomes without internal structure |
| Single-shell | cytoplasm, membrane | most mammalian cells |
| Two-shell | cytoplasm, membrane, wall | yeast, bacteria, plant cells |
| Three-shell | nucleoplasm, envelope, cytoplasm, membrane | cells with a large nucleus |
| Four-shell | nucleoplasm, envelope, cytoplasm, membrane, wall | walled cells with a nucleus |

More layers mean more parameters, most of which a spectrum alone cannot determine: fit with the simplest model that describes the data, and fix the parameters that are known (buffer, radius, membrane thickness).

## Useful relations

- **Membrane capacitance**: C<sub>mem</sub> = ε<sub>0</sub> ε<sub>mem</sub> / d<sub>mem</sub> (F/m²). E.g. ε<sub>mem</sub> = 10, d = 7 nm gives 12.6 mF/m².
- **First crossover** (single-shell, conducting cytoplasm): roughly f<sub>co1</sub> ≈ √2 σ<sub>m</sub> / (2π r C<sub>mem</sub>): it rises with the medium conductivity and falls with cell size and membrane capacitance.
- Conductivity units: 1 S/m = 10 000 µS/cm, so 200 µS/cm = 0.02 S/m.

## Further reading

- H. A. Pohl, *Dielectrophoresis*, Cambridge University Press (1978).
- T. B. Jones, *Electromechanics of Particles*, Cambridge University Press (1995).
- [OpenDEP: An Open-Source Platform for Dielectrophoresis Spectra Acquisition and Analysis](https://pubs.acs.org/doi/10.1021/acsomega.3c06052), *ACS Omega*.
- [MyDEP](https://mydepsoftware.github.io/), another program for DEP models.
