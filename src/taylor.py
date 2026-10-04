"""Série de Taylor de f(x) = x * e^x (em torno de 0, ou seja, Maclaurin).

Derivadas feitas à mão (sem Sympy):
    f(x)    = x e^x
    f'(x)   = (x + 1) e^x
    f''(x)  = (x + 2) e^x
    f^(n)(x) = (x + n) e^x      (indução, ver README)
    f^(n)(0) = n

    T_N(x) = sum_{n=1..N} n x^n / n!  =  x * sum_{k=0..N-1} x^k / k!

Uso:
    python3 src/taylor.py        # exemplos
    python3 src/taylor.py 1.5 12 # x = 1.5 com N = 12
"""
import math
import sys

LN2 = math.log(2.0)


# ---------------------------------------------------------------- derivadas
def derivada(n, x):
    """n-ésima derivada de x*e^x, obtida à mão: (x + n) e^x."""
    return (x + n) * math.exp(x)


# ----------------------------------------------------------- implementações
def taylor_ingenua(x, N):
    """Soma n*x^n/n! recalculando potência e fatorial a cada termo (baseline)."""
    soma = 0.0
    for n in range(1, N + 1):
        soma += n * x**n / math.factorial(n)
    return soma


def taylor_recorrencia(x, N):
    """Reaproveita o termo anterior: t_k = t_{k-1} * x / k (sem fatorial)."""
    termo = 1.0
    soma = 1.0
    for k in range(1, N):
        termo *= x / k
        soma += termo
    return x * soma


def taylor_horner(x, N):
    """Horner: 1 + x/1 (1 + x/2 (1 + x/3 (...))), com N-1 multiplicações."""
    acc = 1.0
    for k in range(N - 1, 0, -1):
        acc = 1.0 + acc * x / k
    return x * acc


def taylor_otimizada(x, N):
    """Redução de argumento + Horner.

    e^x = 2^m * e^r, com m = round(x / ln 2) e |r| <= ln2/2 ~ 0.347.
    A série só precisa convergir para |r| pequeno, então poucos termos bastam
    em qualquer x. Aqui N é o número de termos da série de e^r, e 2^m é
    aplicado exatamente com ldexp (só mexe no expoente do float).
    """
    m = round(x / LN2)
    r = x - m * LN2
    acc = 1.0
    for k in range(N - 1, 0, -1):
        acc = 1.0 + acc * r / k
    return x * math.ldexp(acc, m)


def taylor_vetor(x, N):
    """Mesma recorrência de taylor_recorrencia, mas para um vetor NumPy x (gráficos)."""
    import numpy as np
    x = np.asarray(x, dtype=float)
    termo = np.ones_like(x)
    soma = np.ones_like(x)
    for k in range(1, N):
        termo = termo * x / k
        soma = soma + termo
    return x * soma


def derivada_vetor(n, x):
    """(x + n) e^x para um vetor NumPy x (mesma fórmula de derivada)."""
    import numpy as np
    x = np.asarray(x, dtype=float)
    return (x + n) * np.exp(x)


METODOS = {
    "ingênua": taylor_ingenua,
    "recorrência": taylor_recorrencia,
    "Horner": taylor_horner,
    "otimizada (redução + Horner)": taylor_otimizada,
}


# ---------------------------------------------------------- escolha do N
def resto_lagrange(N, a):
    """Cota de |f(x) - T_N(x)| para |x| <= a.

    R_N(x) = f^(N+1)(xi) x^(N+1) / (N+1)!  com f^(N+1)(xi) = (xi + N + 1) e^xi
    e |xi| <= a  =>  |R_N| <= (N + 1 + a) e^a a^(N+1) / (N+1)!
    """
    return (N + 1 + a) * math.exp(a) * a ** (N + 1) / math.factorial(N + 1)


cota_lagrange = resto_lagrange


def escolher_N(a, tol=1e-12):
    """Menor N (série simples) com cota de Lagrange < tol em [-a, a]."""
    N = 1
    while resto_lagrange(N, a) >= tol:
        N += 1
    return N


def escolher_N_reduzido(tol=1e-15):
    """Menor nº de termos para e^r em |r| <= ln2/2, com erro relativo < tol.

    Resto de e^r com M termos: <= e^a a^M / M!; relativo a e^r >= e^-a.
    """
    a = LN2 / 2
    M = 1
    while math.exp(2 * a) * a**M / math.factorial(M) >= tol:
        M += 1
    return M


def main():
    x = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    exato = x * math.exp(x)
    print(f"f({x}) = x*e^x, valor de referência (math.exp): {exato!r}\n")
    for nome, f in METODOS.items():
        v = f(x, N)
        print(f"{nome:30s} N={N:<3d} -> {v!r}   erro abs = {abs(v - exato):.2e}")
    print()
    print("Conferindo f^(n)(0) = n:", [round(derivada(n, 0.0)) for n in range(1, 8)])
    for a in (1, 2, 5):
        print(f"N mínimo p/ erro < 1e-12 em [-{a}, {a}] (Lagrange): {escolher_N(a)}")
    print(f"Termos de e^r na versão otimizada (|r| <= ln2/2): {escolher_N_reduzido()}")


if __name__ == "__main__":
    main()
