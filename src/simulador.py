"""Simulador interativo - EP 1 Cálculo II: Série de Taylor de y = x·e^x.

Toda a matemática está em taylor.py; aqui fica só a interface (matplotlib.widgets).
Execute (da raiz do projeto):  python3 src/simulador.py

Comparação automática: ao soltar um slider, os valores anteriores ficam no gráfico como
linhas tracejadas (a mais recente em laranja) e o painel de resultados mostra
"antes" x "agora".
"""
import math
import os
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons, Button

import taylor as ty

# --- Nomes das visões e modos -----------------------------------------------
APROX = "Aproximação f(x) × T_N(x)"
ERRO_N = "Erro × N (escolha do N)"
METODOS = "Métodos: erro × tempo"
DERIV = "Derivadas e série"
TABELA = "Tabela de valores"
VISOES = [APROX, ERRO_N, METODOS, DERIV, TABELA]

TODOS = "Todos os métodos"
SIMPLES, OTIMIZADA = "Série simples", "Otimizada"
MODOS = {METODOS: [TODOS] + list(ty.METODOS), TABELA: [SIMPLES, OTIMIZADA]}

# (chave, rótulo, mínimo, máximo, padrão, símbolo curto, passo)
SLIDERS = {
    APROX: [("N", "Termos N", 1, 40, 3, "N", 1),
            ("a", "Intervalo [−a, a]", 1, 10, 4, "a", 0.5),
            ("x", "Ponto de teste x", -10, 10, 1, "x", 0.1)],
    ERRO_N: [("x", "Ponto de teste x", -10, 10, 2, "x", 0.1),
             ("tol", "Tolerância (10^k)", -15, -2, -12, "tol", 1)],
    METODOS: [("a", "Intervalo [−a, a]", 1, 10, 5, "a", 0.5),
              ("nmax", "N máximo", 10, 60, 40, "Nmáx", 2)],
    DERIV: [("N", "Termos N", 1, 20, 5, "N", 1),
            ("x", "Ponto x", -3, 3, 1, "x", 0.1)],
    TABELA: [("N", "Termos N", 1, 40, 16, "N", 1)],
}

XS_TABELA = [-5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10]
TOL_PADRAO = 1e-12
PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz do projeto

# --- Cores -------------------------------------------------------------------
FUNDO, CARTAO, DESTAQUE = "#f3f5fa", "#ffffff", "#2563eb"
TEXTO, APAGADO, BORDA = "#1f2937", "#6b7280", "#e5e7eb"
COR_RECENTE, COR_ANTIGA, COR_ALERTA, COR_OK = "#f59e0b", "#9ca3af", "#dc2626", "#16a34a"
CORES_METODO = dict(zip(ty.METODOS, ["#6b7280", "#f59e0b", "#16a34a", "#dc2626"]))

estado = {"visao": APROX, "modo": None}
valores_salvos = {}
comparacao = {"ref": None, "historico": []}
ctl = {"axes": [], "sliders": {}, "radio": None}
cache_medicao = {}           # (a, nmax) -> {método: [(N, µs, erro)]}

# --- Janela e painel esquerdo ------------------------------------------------
fig = plt.figure(figsize=(14, 8), facecolor=FUNDO)
try:
    fig.canvas.manager.set_window_title("Simulador - Série de Taylor de x·e^x")
except Exception:
    pass

ax_cartao = fig.add_axes([0.015, 0.012, 0.31, 0.976], facecolor=CARTAO)
ax_cartao.set_xticks([]); ax_cartao.set_yticks([])
for s in ax_cartao.spines.values():
    s.set_color(BORDA)

fig.text(0.035, 0.95, "Série de Taylor de y = x·eˣ", fontsize=16, weight="bold", color=TEXTO)
fig.text(0.035, 0.925, "EP 1 · Cálculo II · simulador interativo", fontsize=9, color=APAGADO)
fig.text(0.035, 0.895, "1. ESCOLHA A VISÃO", fontsize=8, weight="bold", color=DESTAQUE)
fig.text(0.035, 0.545, "3. AJUSTE OS PARÂMETROS", fontsize=8, weight="bold", color=DESTAQUE)
fig.text(0.035, 0.022, "Dica: ao soltar um slider, o valor anterior fica tracejado no gráfico.",
         fontsize=7.5, color=APAGADO)
texto_modo = fig.text(0.035, 0.715, "", fontsize=8, weight="bold", color=DESTAQUE)

ax_sis = fig.add_axes([0.03, 0.745, 0.28, 0.145], facecolor=CARTAO)
radio_visao = RadioButtons(ax_sis, VISOES, activecolor=DESTAQUE, radio_props={"s": 70})
ax_info = fig.add_axes([0.03, 0.05, 0.28, 0.245], facecolor="#f9fafb")
ax_a = fig.add_axes([0.41, 0.56, 0.56, 0.36])
ax_b = fig.add_axes([0.41, 0.09, 0.56, 0.36])


def estilizar_radio(radio, ax):
    for s in ax.spines.values():
        s.set_visible(False)
    for lab in radio.labels:
        lab.set_fontsize(10); lab.set_color(TEXTO)


estilizar_radio(radio_visao, ax_sis)


# --- Funções auxiliares de cálculo ------------------------------------------
def exato(x):
    return x * math.exp(x)


def erro_rel(v, x):
    e = exato(x)
    return abs(v - e) / abs(e) if e != 0 else abs(v)


def piso(v):
    """Evita log(0) nos gráficos de erro."""
    return np.maximum(v, 1e-18)


def sci(v):
    return f"{v:.2e}"


def medir_metodos(a, nmax):
    """Tempo médio por chamada (µs) e maior erro relativo em 24 pontos de [-a, a]."""
    xs = [-a + 2 * a * (i + 0.5) / 24 for i in range(24)]
    saida = {}
    for nome, fn in ty.METODOS.items():
        pts = []
        for N in range(2, int(nmax) + 1, 2):
            t0 = time.perf_counter()
            for _ in range(30):
                for x in xs:
                    fn(x, N)
            dt = (time.perf_counter() - t0) / (30 * len(xs)) * 1e6
            pts.append((N, dt, max(erro_rel(fn(x, N), x) for x in xs)))
        saida[nome] = pts
    return saida


# --- Cálculo por visão (só chama taylor.py) ---------------------------------
def calcular(visao, modo, p):
    """Devolve as séries para os gráficos e a lista de resultados do painel."""
    if visao == APROX:
        N, x0 = int(round(p["N"])), p["x"]
        A = max(p["a"], abs(x0))
        xs = np.linspace(-A, A, 500)
        f = xs * np.exp(xs)
        T = ty.taylor_vetor(xs, N)
        v = ty.taylor_recorrencia(x0, N)
        info = [("T_N(x)", f"{v:.10g}"), ("f(x) exato", f"{exato(x0):.10g}"),
                ("Erro absoluto", sci(abs(v - exato(x0)))),
                ("Erro relativo", sci(erro_rel(v, x0))),
                ("Cota de Lagrange", sci(ty.cota_lagrange(N, A))),
                ("N mín. (tol 1e-12)", str(ty.escolher_N(A, TOL_PADRAO)))]
        return dict(xs=xs, f=f, T=T, A=A, N=N, x0=x0, v=v, info=info)

    if visao == ERRO_N:
        x0, tol = p["x"], 10.0 ** round(p["tol"])
        Ns = np.arange(1, 46)
        ex = exato(x0)
        simples = np.array([ty.taylor_recorrencia(x0, int(n)) for n in Ns])
        otim = np.array([ty.taylor_otimizada(x0, int(n)) for n in Ns])
        err_abs = np.abs(simples - ex)
        rel_s = err_abs / abs(ex) if ex != 0 else err_abs
        rel_o = np.abs(otim - ex) / abs(ex) if ex != 0 else np.abs(otim - ex)
        cota = np.array([ty.cota_lagrange(int(n), abs(x0)) for n in Ns])
        n_sug = ty.escolher_N(abs(x0), tol)
        ok = np.nonzero(err_abs < tol)[0]
        n_emp = str(Ns[ok[0]]) if len(ok) else "não atingiu"
        info = [("Tolerância", f"{tol:.0e}"), ("N (Lagrange)", str(n_sug)),
                ("N empírico (erro < tol)", n_emp),
                ("Erro real em N (Lagr.)",
                 sci(err_abs[min(n_sug, 45) - 1]) if n_sug <= 45 else ">45"),
                ("Termos da otimizada", str(ty.escolher_N_reduzido()))]
        return dict(Ns=Ns, rel_s=rel_s, rel_o=rel_o, err_abs=err_abs, cota=cota,
                    tol=tol, n_sug=n_sug, x0=x0, info=info)

    if visao == METODOS:
        chave = (p["a"], p["nmax"])
        med = cache_medicao.get(chave)
        info = []
        if med:
            for nome, pts in med.items():
                ok = [q for q in pts if q[2] < 1e-10]
                info.append((nome.split(" ")[0], f"N={ok[0][0]} · {ok[0][1]:.2f} µs"
                             if ok else "não atingiu 1e-10"))
        else:
            info = [("Status", "clique em Medir")]
        return dict(med=med, info=info)

    if visao == DERIV:
        N, x0 = int(round(p["N"])), p["x"]
        xs = np.linspace(-4, 2, 300)
        ders = [ty.derivada_vetor(n, xs) for n in range(4)]
        somas = [ty.taylor_recorrencia(x0, n) for n in range(1, N + 1)]
        info = [("f(x)", f"{ty.derivada(0, x0):.6g}"), ("f'(x)", f"{ty.derivada(1, x0):.6g}"),
                ("f''(x)", f"{ty.derivada(2, x0):.6g}"), ("f'''(x)", f"{ty.derivada(3, x0):.6g}"),
                ("Último termo xᴺ/(N−1)!", sci(x0**N / math.factorial(N - 1))),
                ("T_N(x)", f"{somas[-1]:.8g}")]
        return dict(xs=xs, ders=ders, somas=somas, x0=x0, N=N, info=info)

    N = int(round(p["N"]))
    fn = ty.taylor_recorrencia if modo == SIMPLES else ty.taylor_otimizada
    ap = [fn(x, N) for x in XS_TABELA]
    er = [erro_rel(v, x) for v, x in zip(ap, XS_TABELA)]
    pior = int(np.argmax(er))
    info = [("Método", modo), ("Termos N", str(N)),
            ("Maior erro relativo", sci(er[pior])), ("Pior x", str(XS_TABELA[pior]))]
    return dict(ap=ap, er=er, info=info)


# --- Controles (reconstruídos a cada troca de visão) ------------------------
def params_atuais():
    return {k: s.val for k, s in ctl["sliders"].items()}


def salvar_valores():
    if ctl["sliders"]:
        valores_salvos[estado["visao"]] = params_atuais()


def montar_controles(padrao=False):
    for ax in ctl["axes"]:
        fig.delaxes(ax)
    ctl.update(axes=[], sliders={}, radio=None)
    visao = estado["visao"]

    modos = MODOS.get(visao)
    texto_modo.set_text("2. ESCOLHA O MODO" if modos else "")
    if modos:
        h = 0.021 * len(modos) + 0.02
        ax = fig.add_axes([0.03, 0.705 - h, 0.28, h], facecolor=CARTAO)
        radio = RadioButtons(ax, modos, active=modos.index(estado["modo"]),
                             activecolor=DESTAQUE, radio_props={"s": 55})
        estilizar_radio(radio, ax)
        for lab in radio.labels:
            lab.set_fontsize(9)
        radio.on_clicked(trocar_modo)
        ctl["axes"].append(ax); ctl["radio"] = radio

    salvos = {} if padrao else valores_salvos.get(visao, {})
    for i, (chave, rotulo, lo, hi, v0, _, passo) in enumerate(SLIDERS[visao]):
        ax = fig.add_axes([0.175, 0.50 - 0.045 * i, 0.10, 0.022], facecolor=BORDA)
        fmt = "%.0f" if passo >= 1 else "%.1f"
        s = Slider(ax, rotulo, lo, hi, valinit=salvos.get(chave, v0), valstep=passo,
                   valfmt=fmt, color=DESTAQUE, initcolor="none")
        s.label.set_fontsize(8.5); s.label.set_color(TEXTO)
        s.valtext.set_fontsize(8.5); s.valtext.set_color(TEXTO)
        s.on_changed(lambda _: desenhar())
        ctl["axes"].append(ax); ctl["sliders"][chave] = s


def reiniciar_comparacao():
    comparacao["ref"] = params_atuais()
    comparacao["historico"] = []


def trocar_visao(rotulo):
    salvar_valores()
    estado["visao"] = rotulo
    estado["modo"] = MODOS[rotulo][0] if rotulo in MODOS else None
    montar_controles()
    reiniciar_comparacao()
    desenhar()


def trocar_modo(rotulo):
    estado["modo"] = rotulo
    reiniciar_comparacao()
    desenhar()


def limpar_comparacoes(_=None):
    reiniciar_comparacao()
    desenhar()


def restaurar_padrao(_=None):
    montar_controles(padrao=True)
    reiniciar_comparacao()
    desenhar()


def medir(_=None):
    if estado["visao"] != METODOS:
        radio_visao.set_active(VISOES.index(METODOS))   # chama trocar_visao
    p = params_atuais()
    texto_status.set_text("medindo...")
    fig.canvas.draw()
    cache_medicao[(p["a"], p["nmax"])] = medir_metodos(p["a"], p["nmax"])
    texto_status.set_text("")
    desenhar()


def salvar_png(_=None):
    pasta = os.path.join(PASTA, "resultados")
    os.makedirs(pasta, exist_ok=True)
    nome = "simulador_" + "".join(c if c.isalnum() else "_" for c in estado["visao"]) + ".png"
    caminho = os.path.join(pasta, nome)
    fig.savefig(caminho, dpi=130, facecolor=fig.get_facecolor())
    texto_status.set_text(f"salvo em resultados/{nome}")
    fig.canvas.draw_idle()


def ao_soltar_mouse(_):
    """Ao soltar um slider, o valor anterior vira um 'fantasma' de comparação."""
    p = params_atuais()
    if comparacao["ref"] is not None and comparacao["ref"] != p:
        comparacao["historico"] = (comparacao["historico"] + [comparacao["ref"]])[-3:]
        comparacao["ref"] = p
        desenhar()


def fantasmas(p):
    """Lista (calc, rótulo, cor, espessura) dos valores anteriores, do mais antigo ao mais novo."""
    if estado["visao"] == METODOS:
        return []
    antigos = list(comparacao["historico"])
    if comparacao["ref"] is not None and comparacao["ref"] != p:
        antigos.append(comparacao["ref"])
    antigos = antigos[-4:]
    simbolos = {c[0]: c[5] for c in SLIDERS[estado["visao"]]}
    saida = []
    for i, gp in enumerate(antigos):
        mudou = [f"{simbolos[k]}={gp[k]:.4g}" for k in p if gp[k] != p[k]]
        rotulo = "antes: " + ", ".join(mudou) if mudou else "antes"
        recente = i == len(antigos) - 1
        saida.append((calcular(estado["visao"], estado["modo"], gp), rotulo,
                      COR_RECENTE if recente else COR_ANTIGA, 2.0 if recente else 1.4))
    return saida


# --- Desenho -----------------------------------------------------------------
def estilizar_eixo(ax, titulo, xlabel, ylabel):
    ax.clear()
    ax.set_axis_on()
    ax.set_facecolor(CARTAO)
    ax.set_title(titulo, fontsize=11, color=TEXTO, loc="left", pad=8)
    ax.set_xlabel(xlabel, fontsize=9, color=APAGADO)
    ax.set_ylabel(ylabel, fontsize=9, color=APAGADO)
    ax.grid(True, color=BORDA, lw=0.8)
    ax.tick_params(colors=APAGADO, labelsize=8.5)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(BORDA)
    ax.set_aspect("auto")


def desenhar_resultados(atual, fant):
    ax_info.clear()
    ax_info.set_xticks([]); ax_info.set_yticks([])
    for s in ax_info.spines.values():
        s.set_color(BORDA)
    ax_info.text(0.04, 0.93, "Resultados", fontsize=10, weight="bold", color=TEXTO, va="center")
    antes = fant[-1][0]["info"] if fant else None
    if antes:
        ax_info.text(0.64, 0.93, "antes", fontsize=8, color=COR_RECENTE, ha="right", va="center")
    ax_info.text(0.96, 0.93, "agora", fontsize=8, color=DESTAQUE, ha="right", va="center")
    for i, (rotulo, texto) in enumerate(atual["info"]):
        y = 0.80 - 0.115 * i
        ax_info.text(0.04, y, rotulo, fontsize=8, color=APAGADO, va="center")
        if antes and i < len(antes):
            ax_info.text(0.64, y, antes[i][1], fontsize=7.5, color=COR_RECENTE,
                         ha="right", va="center")
        ax_info.text(0.96, y, texto, fontsize=8.5, weight="bold", color=TEXTO,
                     ha="right", va="center")


def desenhar_aprox(atual, fant):
    A, N = atual["A"], atual["N"]
    estilizar_eixo(ax_a, f"f(x) = x·eˣ  e  T_{N}(x) = x·Σ xᵏ/k!   (k = 0 … {N - 1})", "x", "y")
    estilizar_eixo(ax_b, "Erro absoluto |f(x) − T_N(x)|  (escala log)", "x", "erro")
    for calc, rot, cor, lw in fant:
        ax_a.plot(calc["xs"], calc["T"], "--", color=cor, lw=lw, label=rot)
        ax_b.semilogy(calc["xs"], piso(np.abs(calc["f"] - calc["T"])), "--", color=cor, lw=lw)
    ax_a.plot(atual["xs"], atual["f"], color=TEXTO, lw=2.2, label="f(x) = x·eˣ")
    ax_a.plot(atual["xs"], atual["T"], color=DESTAQUE, lw=2.6, label=f"T_{N}(x) agora")
    ax_a.plot([atual["x0"]], [exato(atual["x0"])], "o", color=COR_ALERTA, ms=7)
    ax_a.plot([atual["x0"]], [atual["v"]], "x", color=DESTAQUE, ms=9, mew=2)
    fmax = max(atual["f"].max(), 1.0)
    ax_a.set_xlim(-A, A)
    ax_a.set_ylim(-0.15 * fmax - 0.5, 1.1 * fmax)
    ax_b.semilogy(atual["xs"], piso(np.abs(atual["f"] - atual["T"])), color=DESTAQUE, lw=2.6,
                  label="agora")
    ax_b.axvline(atual["x0"], color=COR_ALERTA, ls=":", lw=1.2)
    ax_b.set_xlim(-A, A)


def desenhar_erro_n(atual, fant):
    estilizar_eixo(ax_a, f"Erro relativo em x = {atual['x0']:.1f} × nº de termos N",
                   "N", "erro relativo")
    estilizar_eixo(ax_b, "Cota de Lagrange × erro real (absoluto) — a cota sempre vale",
                   "N", "erro absoluto")
    for calc, rot, cor, lw in fant:
        ax_a.semilogy(calc["Ns"], piso(calc["rel_s"]), "--", color=cor, lw=lw, label=rot)
    ax_a.semilogy(atual["Ns"], piso(atual["rel_s"]), color=DESTAQUE, lw=2.6, label="série simples")
    ax_a.semilogy(atual["Ns"], piso(atual["rel_o"]), color=COR_OK, lw=2.0,
                  label="otimizada (redução + Horner)")
    ax_a.axhline(atual["tol"], color=COR_ALERTA, ls="-.", lw=1.3, label="tolerância")
    ax_a.axvline(atual["n_sug"], color=APAGADO, ls="--", lw=1.2,
                 label=f"N (Lagrange) = {atual['n_sug']}")
    ax_b.semilogy(atual["Ns"], piso(atual["cota"]), color=COR_RECENTE, lw=2.2, label="cota de Lagrange")
    ax_b.semilogy(atual["Ns"], piso(atual["err_abs"]), color=DESTAQUE, lw=2.2, label="erro real")
    ax_b.axhline(atual["tol"], color=COR_ALERTA, ls="-.", lw=1.3, label="tolerância")
    ax_b.axvline(atual["n_sug"], color=APAGADO, ls="--", lw=1.2)


def desenhar_metodos(atual, modo):
    estilizar_eixo(ax_a, "Erro máximo em [−a, a] × tempo por chamada", "tempo por chamada (µs)",
                   "erro relativo máximo")
    estilizar_eixo(ax_b, "Tempo por chamada × N", "N (nº de termos)", "tempo (µs)")
    med = atual["med"]
    if not med:
        for ax in (ax_a, ax_b):
            ax.text(0.5, 0.5, "Clique em 'Medir tempos'\n(a medição leva alguns segundos)",
                    transform=ax.transAxes, ha="center", va="center", fontsize=11, color=APAGADO)
        return
    for nome, pts in med.items():
        destaque = modo in (TODOS, nome)
        kw = dict(color=CORES_METODO[nome], lw=2.2 if destaque else 1.0,
                  alpha=1 if destaque else 0.3, marker="o", ms=3, label=nome)
        ax_a.loglog([q[1] for q in pts], piso(np.array([q[2] for q in pts])), **kw)
        ax_b.plot([q[0] for q in pts], [q[1] for q in pts], **kw)


def desenhar_deriv(atual):
    N, x0 = atual["N"], atual["x0"]
    estilizar_eixo(ax_a, "f⁽ⁿ⁾(x) = (x + n)·eˣ   →   f⁽ⁿ⁾(0) = n", "x", "y")
    estilizar_eixo(ax_b, f"Somas parciais T_n({x0:.1f}) convergindo para f({x0:.1f})",
                   "n (nº de termos)", "T_n(x)")
    nomes = ["f", "f '", "f ''", "f '''"]
    cores = [TEXTO, DESTAQUE, COR_OK, COR_RECENTE]
    for n, (d, nome, cor) in enumerate(zip(atual["ders"], nomes, cores)):
        ax_a.plot(atual["xs"], d, color=cor, lw=2.4 if n == 0 else 1.6, label=f"{nome}(x) = (x+{n})eˣ")
        ax_a.plot([x0], [ty.derivada(n, x0)], "o", color=cor, ms=6)
    ax_a.axvline(x0, color=APAGADO, ls=":", lw=1.2)
    ax_a.set_ylim(-1, 15)
    ns = np.arange(1, N + 1)
    ax_b.plot(ns, atual["somas"], "o-", color=DESTAQUE, lw=2, label="T_n(x)")
    ax_b.axhline(exato(x0), color=COR_ALERTA, ls="-.", lw=1.4, label="f(x) exato")


def desenhar_tabela(atual, modo):
    estilizar_eixo(ax_a, f"Valores fixos — {modo}", "", "")
    ax_a.set_axis_off()
    linhas = [[f"{x:g}", f"{exato(x):.10g}", f"{v:.10g}", sci(e)]
              for x, v, e in zip(XS_TABELA, atual["ap"], atual["er"])]
    tab = ax_a.table(cellText=linhas, colLabels=["x", "f(x) exato", "Taylor", "erro relativo"],
                     loc="center", cellLoc="right")
    tab.auto_set_font_size(False)
    tab.set_fontsize(9)
    tab.scale(1, 1.55)
    for (r, _), cel in tab.get_celld().items():
        cel.set_edgecolor(BORDA)
        if r == 0:
            cel.set_facecolor(BORDA); cel.set_text_props(weight="bold", color=TEXTO)
    estilizar_eixo(ax_b, "Erro relativo por x (escala log)", "x", "erro relativo")
    pos = np.arange(len(XS_TABELA))
    ax_b.bar(pos, piso(np.array(atual["er"])), color=DESTAQUE, bottom=0)
    ax_b.set_yscale("log")
    ax_b.set_ylim(1e-18, 10)
    ax_b.set_xticks(pos, [f"{x:g}" for x in XS_TABELA])


def desenhar():
    visao, modo, p = estado["visao"], estado["modo"], params_atuais()
    atual = calcular(visao, modo, p)
    fant = fantasmas(p)

    if visao == APROX:
        desenhar_aprox(atual, fant)
    elif visao == ERRO_N:
        desenhar_erro_n(atual, fant)
    elif visao == METODOS:
        desenhar_metodos(atual, modo)
    elif visao == DERIV:
        desenhar_deriv(atual)
    else:
        desenhar_tabela(atual, modo)

    if visao != TABELA:
        for ax in (ax_a, ax_b):
            if ax.get_legend_handles_labels()[0]:
                ax.legend(loc="best", fontsize=8, frameon=True, framealpha=0.9, edgecolor=BORDA)
    desenhar_resultados(atual, fant)
    fig.canvas.draw_idle()


# --- Botões e eventos --------------------------------------------------------
def criar_botao(pos, texto, acao):
    ax = fig.add_axes(pos)
    b = Button(ax, texto, color=BORDA, hovercolor="#d1d5db")
    b.label.set_fontsize(8.5); b.label.set_color(TEXTO)
    b.on_clicked(acao)
    return b


botao_limpar = criar_botao([0.03, 0.355, 0.135, 0.035], "Limpar comparações", limpar_comparacoes)
botao_padrao = criar_botao([0.175, 0.355, 0.135, 0.035], "Restaurar padrão", restaurar_padrao)
botao_medir = criar_botao([0.03, 0.31, 0.135, 0.035], "Medir tempos", medir)
botao_png = criar_botao([0.175, 0.31, 0.135, 0.035], "Salvar PNG", salvar_png)
texto_status = fig.text(0.035, 0.30, "", fontsize=7.5, color=APAGADO)
radio_visao.on_clicked(trocar_visao)
fig.canvas.mpl_connect("button_release_event", ao_soltar_mouse)

montar_controles()
reiniciar_comparacao()
desenhar()

if __name__ == "__main__":
    plt.show()
