import numpy as np
from typing import Literal

Models = Literal["Kato", "Eimerl", "Zhang", "Tamosaukas"]


def no(l: float, model: Models = "Eimerl"):
    """Get ordinary refractive index of BBO

    Args:
        l (float): wavelength in um
        model (Models, optional): dispertion model. Defaults to "Eimerl".

    Returns:
        float: no
    """
    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Eimerl-o
    if model == "Eimerl" and 0.22 <= l <= 1.06:
        return np.sqrt(2.7405 + (0.0184) / (l**2 - 0.0179) - 0.0155 * l**2)

    # From https://sci-hub.st/10.1109/JQE.1986.1073097 Kato et al. 1986 and
    # Interference with correlated photons: Five quantum mechanics experiments for  undergraduates eq. B5
    elif model == "Kato" and 0.22 <= l <= 1.06:
        return np.sqrt(2.7359 + 0.01878 / (l**2 - 0.01822) - 0.01354 * l**2)

    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Tamosauskas-o
    elif model == "Tamosaukas" and 0.188 <= l <= 5.2:
        return np.sqrt(
            (0.90291 * l**2) / (l**2 - 0.003926)
            + (0.83155 * l**2) / (l**2 - 0.018786)
            + (0.76536 * l**2) / (l**2 - 60.01)
            + 1
        )

    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Zhang-o
    elif model == "Zhang" and 0.64 <= l <= 3.18:
        return np.sqrt(
            2.7359
            + (0.01878) / (l**2 - 0.01822)
            - 0.01471 * l**2
            + 0.0006081 * l**4
            - 0.00006740 * l**6
        )
    else:
        raise ValueError


def ne(l, model: Models = "Eimerl"):
    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Eimerl-e
    if model == "Eimerl" and 0.22 <= l <= 1.06:
        return np.sqrt(2.3730 + (0.0128) / (l**2 - 0.0156) - 0.0044 * l**2)

    # From https://sci-hub.st/10.1109/JQE.1986.1073097 Kato et al. 1986 and
    # Interference with correlated photons: Five quantum mechanics experiments for  undergraduates eq B5
    elif model == "Kato" and 0.22 <= l <= 1.06:
        return np.sqrt(2.3753 + 0.01224 / (l**2 - 0.01667) + -0.01516 * l**2)

    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Tamosauskas-e
    elif model == "Tamosaukas" and 0.188 <= l <= 5.2:
        return np.sqrt(
            (1.151075 * l**2) / (l**2 - 0.007142)
            + (0.21803 * l**2) / (l**2 - 0.02259)
            + (0.656 * l**2) / (l**2 - 263)
            + 1
        )

    # From https://refractiveindex.info/?shelf=main&book=BaB2O4&page=Zhang-e
    elif model == "Zhang" and 0.64 <= l <= 3.18:
        return np.sqrt(
            2.3753
            + (0.01224) / (l**2 - 0.01667)
            - 0.01627 * l**2
            + 0.0005716 * l**4
            - 0.00006305 * l**6
        )
    else:
        raise ValueError


def neeff(length, angle, model: Models = "Eimerl"):
    return (
        np.cos(angle) ** 2 / no(length, model) ** 2
        + np.sin(angle) ** 2 / ne(length, model) ** 2
    ) ** -0.5
