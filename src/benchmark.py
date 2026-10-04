"""Gera tabela de valores e gráficos (erro x N, erro x tempo, aproximações).

Uso (da raiz do projeto): python3 src/benchmark.py     (salva tudo em resultados/)
"""
import math
import os
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from taylor import (METODOS, escolher_N, escolher_N_reduzido, resto_lagrange,
                    taylor_otimizada, taylor_recorrencia)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "resultados")
os.makedirs(OUT, exist_ok=True)

TOL = 1e-12
A_INTERVALO = 5                      # domínio de interesse: [-5, 5]
N_SIMPLES = escolher_N(1, TOL)       # série simples vale em |x| <= 1
M_OTIMIZADA = escolher_N_reduzido()  # termos de e^r, |r| <= ln2/2
PLOT_STYLE = {"axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 130}
plt.rcParams.update(PLOT_STYLE)


def exato(x):
    return x * math.exp(x)


def erro_rel(v, x):
    e = exato(x)
    return abs(v - e) / abs(e) if e != 0 else abs(v)


def piso(v):
    return max(v, 1e-18)  # evita log(0) nos gráficos


# ------------------------------------------------------------------ tabela
def tabela():
    xs = [-5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10]
    linhas = [
        f"Série simples com N = {N_SIMPLES} (cota de Lagrange < {TOL:g} em [-1, 1]) "
        f"e otimizada com {M_OTIMIZADA} termos de e^r.\n",
        "| x | f(x) = x·e^x (math.exp) | Taylor simples | erro rel. simples "
        "| Taylor otimizada | erro rel. otimizada |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for x in xs:
        s = taylor_recorrencia(x, N_SIMPLES)
        o = taylor_otimizada(x, M_OTIMIZADA)
        linhas.append(
            f"| {x} | {exato(x):.12g} | {s:.12g} | {erro_rel(s, x):.1e} "
            f"| {o:.12g} | {erro_rel(o, x):.1e} |"
        )
    texto = "\n".join(linhas) + "\n"
    with open(os.path.join(OUT, "tabela_valores.md"), "w") as fh:
        fh.write(texto)
    print(texto)


# ----------------------------------------------------------------- gráficos
def grafico_funcao():
    xs = [i / 100 for i in range(-800, 301)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(xs, [exato(x) for x in xs], color="#1f77b4", lw=2)
    ax.plot(-1, -1 / math.e, "o", color="#d62728")
    ax.annotate("mínimo global (−1, −1/e)", (-1, -1 / math.e), (-6.5, -2),
                arrowprops=dict(arrowstyle="->"))
    ax.set(title="f(x) = x·eˣ", xlabel="x", ylabel="f(x)", ylim=(-3, 25))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "1_funcao.png"))
    plt.close(fig)


def grafico_aproximacoes():
    xs = [i / 100 for i in range(-400, 301)]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(xs, [exato(x) for x in xs], "k", lw=2.5, label="f(x) = x·eˣ")
    for N in (1, 2, 3, 5, 10):
        ax.plot(xs, [taylor_recorrencia(x, N) for x in xs], lw=1.3, label=f"T_{N}")
    ax.set(title="Polinômios de Taylor T_N convergindo para f", xlabel="x",
           ylabel="y", ylim=(-3, 25))
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "2_aproximacoes.png"))
    plt.close(fig)


def grafico_erro_vs_N():
    Ns = list(range(1, 41))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for x in (0.5, 1, 2, 5, -1, -5):
        ax.semilogy(Ns, [piso(erro_rel(taylor_recorrencia(x, N), x)) for N in Ns],
                    label=f"x = {x}")
    ax.axvline(N_SIMPLES, color="gray", ls="--")
    ax.text(N_SIMPLES + 0.4, 1e-3, f"N = {N_SIMPLES}\n(|x| ≤ 1, tol {TOL:g})", fontsize=8)
    ax.set(title="Erro relativo × N (série simples)", xlabel="N (nº de termos)",
           ylabel="erro relativo")
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "3_erro_vs_N.png"))
    plt.close(fig)


def medir(f, N, xs, reps=200):
    """Retorna (tempo médio por chamada em µs, maior erro relativo em xs)."""
    t0 = time.perf_counter()
    for _ in range(reps):
        for x in xs:
            f(x, N)
    dt = (time.perf_counter() - t0) / (reps * len(xs))
    return dt * 1e6, max(erro_rel(f(x, N), x) for x in xs)


def grafico_erro_vs_tempo():
    # 40 pontos em [-5, 5] (nenhum é zero, onde o erro relativo não existe)
    xs = [-A_INTERVALO + (2 * A_INTERVALO) * (i + 0.5) / 40 for i in range(40)]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    cores = ["#7f7f7f", "#ff7f0e", "#2ca02c", "#d62728"]
    resumo = []
    for (nome, f), cor in zip(METODOS.items(), cores):
        pts = [(N, *medir(f, N, xs)) for N in range(2, 45, 2)]
        ax.loglog([p[1] for p in pts], [piso(p[2]) for p in pts], "o-", ms=3,
                  color=cor, label=nome)
        resumo.append((nome, pts))
    ax.set(title="Erro máximo em [−5, 5] × tempo por chamada",
           xlabel="tempo por chamada (µs)", ylabel="erro relativo máximo")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "4_erro_vs_tempo.png"))
    plt.close(fig)

    # resumo: custo para chegar a erro < 1e-10 em [-5, 5]
    linhas = ["| método | menor N com erro < 1e-10 | tempo (µs) |", "|---|---:|---:|"]
    for nome, pts in resumo:
        ok = [p for p in pts if p[2] < 1e-10]
        linhas.append(f"| {nome} | {ok[0][0]} | {ok[0][1]:.2f} |" if ok
                      else f"| {nome} | não atingiu | — |")
    texto = "\n".join(linhas) + "\n"
    with open(os.path.join(OUT, "tempos.md"), "w") as fh:
        fh.write(texto)
    print(texto)


def tabela_N():
    linhas = ["| intervalo [-a, a] | N mínimo (Lagrange < 1e-12) | cota com esse N |",
              "|---:|---:|---:|"]
    for a in (0.5, 1, 2, 5):
        N = escolher_N(a, TOL)
        linhas.append(f"| {a} | {N} | {resto_lagrange(N, a):.1e} |")
    texto = "\n".join(linhas) + "\n"
    with open(os.path.join(OUT, "escolha_N.md"), "w") as fh:
        fh.write(texto)
    print(texto)


if __name__ == "__main__":
    tabela()
    tabela_N()
    grafico_funcao()
    grafico_aproximacoes()
    grafico_erro_vs_N()
    grafico_erro_vs_tempo()
    print("Arquivos gerados em", OUT)
