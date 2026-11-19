"""Règles calendaires utilisées par l'API (TP DevOps AKS | Lucas MAGRET | ESME)."""

__author__ = "Lucas MAGRET"
__school__ = "ESME | Majeure Transformations Digitales | INGE3"
__module__ = "Services Cloud | TP DevOps AKS"
__version__ = "1.0.0"


def est_bissextile(annee: int) -> bool:
    """Divisible par 4, sauf si divisible par 100, à moins d'être divisible par 400."""
    return annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)
