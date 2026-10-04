# EP 1 – Cálculos Complexos com Séries de Taylor

**Tema:** função $y = x\,e^x$ (exponencial × x)

**Integrantes:**
- Pedro Henrique Patricio de Souza
- Cauã Caravalho de Oliveira
- João Pedro Barbosa Moz

**Disciplina:** Cálculo II · **Vídeo:** _(link do YouTube)_

---

## Como rodar

Precisa de Python 3.10 ou mais novo. A partir da pasta raiz do projeto (a que tem este `README.md`):

```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt     # instala numpy e matplotlib
python3 src/simulador.py            # abre a janela interativa (recomendado)
```

Outros comandos, opcionais:

```bash
python3 src/taylor.py               # exemplos de entrada/saída no terminal (x = 1.5, N = 12)
python3 src/taylor.py 2 20          # outro x e outro N
python3 src/benchmark.py            # regenera os gráficos e tabelas de resultados/
```

Para abrir o notebook (`src/serie_taylor_x_exp_x.ipynb`): `pip install jupyter` e depois `jupyter notebook src/`.

**Problemas comuns**
- `ModuleNotFoundError: matplotlib`: o ambiente virtual não está ativo (rode o `source .venv/bin/activate`) ou faltou o `pip install -r requirements.txt`.
- A janela não abre (Linux/WSL): instale o backend gráfico, por exemplo `sudo apt install python3-tk`.
- Na visão "Métodos: erro × tempo" o gráfico começa vazio: clique em **Medir tempos** (leva alguns segundos).

### Simulador interativo (`src/simulador.py`)

Abre uma janela do matplotlib onde dá para mexer nos valores e ver tudo mudar na hora. Ao soltar um
slider, o valor anterior fica tracejado no gráfico (o mais recente em laranja) e o painel
**Resultados** mostra as colunas _antes_ × _agora_. Botões: **Limpar comparações**, **Restaurar
padrão**, **Medir tempos** e **Salvar PNG** (grava em `resultados/`).

| Visão | Sliders | O que mostra |
|---|---|---|
| Aproximação f(x) × T_N(x) | N, intervalo [−a, a], ponto x | f e T_N sobrepostas, erro absoluto em escala log, cota de Lagrange, N mínimo |
| Erro × N (escolha do N) | ponto x, tolerância 10^k | erro relativo × N (série simples e otimizada), cota de Lagrange × erro real |
| Métodos: erro × tempo | intervalo, N máximo, método | os 4 métodos medidos na sua máquina (botão Medir) |
| Derivadas e série | N, ponto x | f, f′, f″, f‴ com a fórmula (x+n)eˣ e as somas parciais convergindo |
| Tabela de valores | N, série simples ou otimizada | tabela dos valores mais usados e erro relativo por x |

Exemplo de saída de `python3 src/taylor.py` (usa só a biblioteca padrão):

```
f(1.5) = x*e^x, valor de referência (math.exp): 6.722533605507097

ingênua                        N=12  -> 6.722533146746746   erro abs = 4.59e-07
recorrência                    N=12  -> 6.722533146746747   erro abs = 4.59e-07
Horner                         N=12  -> 6.722533146746746   erro abs = 4.59e-07
otimizada (redução + Horner)   N=12  -> 6.722533605507098   erro abs = 8.88e-16

Conferindo f^(n)(0) = n: [1, 2, 3, 4, 5, 6, 7]
```

---

## 1. Derivadas (feitas à mão, sem Sympy)

Pela regra do produto, com $(e^x)' = e^x$:

$$f(x) = x e^x$$
$$f'(x) = 1\cdot e^x + x e^x = (x+1)e^x$$
$$f''(x) = e^x + (x+1)e^x = (x+2)e^x$$
$$f'''(x) = (x+3)e^x$$

**Fórmula geral:** $f^{(n)}(x) = (x+n)\,e^x$.

_Prova por indução._ Para $n=1$ vale. Se $f^{(n)}(x) = (x+n)e^x$, então
$f^{(n+1)}(x) = e^x + (x+n)e^x = (x+n+1)e^x$. ∎

Em $x = 0$: $f^{(n)}(0) = n$.

## 2. Série de Taylor (em torno de 0)

$$T_N(x) = \sum_{n=0}^{N} \frac{f^{(n)}(0)}{n!}x^n = \sum_{n=1}^{N}\frac{n\,x^n}{n!} = \sum_{n=1}^{N}\frac{x^n}{(n-1)!} = x\sum_{k=0}^{N-1}\frac{x^k}{k!}$$

Ou seja, $T_N(x) = x\cdot(\text{série de } e^x \text{ com } N \text{ termos})$. O raio de convergência é infinito (teste da razão: $\frac{|x|}{n}\to 0$).

![f(x)](resultados/1_funcao.png)

![Aproximações T_N](resultados/2_aproximacoes.png)

Quanto maior $N$, maior o intervalo em que $T_N$ cola em $f$. Perto de 0 até $T_1(x) = x$ já serve.

> Cada gráfico e tabela deste README está explicado em [`resultados/README.md`](resultados/README.md): o que é, como ler os eixos e por que está no trabalho.

## 3. Propriedades e aproximações

- $f(0) = 0$ e $f'(0) = 1$, então $f(x) \approx x$ perto da origem (aproximação linear).
- $f'(x) = (x+1)e^x = 0 \Rightarrow x = -1$. Como $f''(-1) = e^{-1} > 0$, é **mínimo global**: $f(-1) = -1/e \approx -0{,}3679$.
- $\lim_{x\to-\infty} f(x) = 0$ (o $e^x$ vence o $x$), logo $y=0$ é assíntota horizontal à esquerda.
- $\lim_{x\to+\infty} f(x) = +\infty$.
- Uma primitiva: $\int x e^x\,dx = (x-1)e^x + C$.
- Quadrática: $T_2(x) = x + x^2$. Cúbica: $T_3(x) = x + x^2 + x^3/2$.

## 4. Escolha de N

O resto de Lagrange diz que, para algum $\xi$ entre 0 e $x$,

$$R_N(x) = \frac{f^{(N+1)}(\xi)}{(N+1)!}x^{N+1} = \frac{(\xi+N+1)e^{\xi}}{(N+1)!}x^{N+1}$$

Para $|x|\le a$ isso dá a cota

$$|R_N(x)| \le \frac{(N+1+a)\,e^{a}\,a^{N+1}}{(N+1)!}$$

Fixamos a tolerância em $10^{-12}$ e pegamos o menor $N$ que cumpre a cota (`escolher_N` em `src/taylor.py`):

| intervalo [-a, a] | N mínimo (Lagrange < 1e-12) | cota com esse N |
|---:|---:|---:|
| 0.5 | 12 | 4.4e-13 |
| 1 | 16 | 1.4e-13 |
| 2 | 21 | 6.6e-13 |
| 5 | 35 | 2.4e-13 |

**N = 16** é o limite da série simples, válido para $|x| \le 1$. Em $x=5$ ela precisaria de $N=35$ e ainda sofre com cancelamento para $x<0$ (termos grandes de sinais alternados).

O gráfico confirma na prática: o erro cai até o piso do `float` (~$10^{-16}$) e a linha tracejada marca o $N$ escolhido.

![Erro × N](resultados/3_erro_vs_N.png)

## 5. Código otimizado

Quatro versões em `src/taylor.py`:

| versão | ideia |
|---|---|
| `taylor_ingenua` | $n\,x^n/n!$ com potência e fatorial recalculados a cada termo |
| `taylor_recorrencia` | cada termo sai do anterior: $t_k = t_{k-1}\cdot x/k$ |
| `taylor_horner` | $1 + \frac{x}{1}\bigl(1+\frac{x}{2}(1+\dots)\bigr)$, sem guardar termos |
| `taylor_otimizada` | **redução de argumento** + Horner |

A otimizada usa $e^x = 2^m\,e^r$ com $m = \mathrm{round}(x/\ln 2)$ e $|r|\le \ln 2/2 \approx 0{,}35$. A série só precisa funcionar para $r$ pequeno (13 termos dão erro relativo ~$10^{-16}$ para qualquer $x$), e $2^m$ é aplicado com `math.ldexp`, que só altera o expoente do float. O resultado é $x\cdot 2^m\,e^r$. É a mesma ideia que bibliotecas matemáticas reais usam.

## 6. Tabela de valores

Série simples com N = 16 e otimizada com 13 termos de $e^r$:

| x | f(x) = x·e^x (math.exp) | Taylor simples | erro rel. simples | Taylor otimizada | erro rel. otimizada |
|---:|---:|---:|---:|---:|---:|
| -5 | -0.0336897349954 | -0.0055968989139 | 8.3e-01 | -0.0336897349954 | 4.1e-16 |
| -2 | -0.270670566473 | -0.270670560872 | 2.1e-08 | -0.270670566473 | 2.1e-16 |
| -1 | -0.367879441171 | -0.367879441171 | 1.2e-13 | -0.367879441171 | 0.0e+00 |
| -0.5 | -0.303265329856 | -0.303265329856 | 1.8e-16 | -0.303265329856 | 0.0e+00 |
| 0 | 0 | 0 | 0.0e+00 | 0 | 0.0e+00 |
| 0.5 | 0.82436063535 | 0.82436063535 | 2.7e-16 | 0.82436063535 | 0.0e+00 |
| 1 | 2.71828182846 | 2.71828182846 | 1.8e-14 | 2.71828182846 | 1.6e-16 |
| 2 | 14.7781121979 | 14.7781121908 | 4.8e-10 | 14.7781121979 | 1.2e-16 |
| 5 | 742.065795513 | 742.014586857 | 6.9e-05 | 742.065795513 | 1.5e-16 |
| 10 | 220264.657948 | 209528.869686 | 4.9e-02 | 220264.657948 | 5.3e-16 |

Fora de $|x|\le 1$ a série simples com $N=16$ perde precisão (ex.: $x=10$ erra 5%), e a otimizada continua no piso do `float`.

## 7. Erro × tempo de execução

Erro relativo máximo em 40 pontos de $[-5,5]$ contra o tempo médio por chamada, variando $N$ de 2 a 44:

![Erro × tempo](resultados/4_erro_vs_tempo.png)

Custo para chegar a erro < $10^{-10}$ em $[-5,5]$ (tempos dependem da máquina):

| método | menor N com erro < 1e-10 | tempo (µs) |
|---|---:|---:|
| ingênua | 32 | 3.67 |
| recorrência | 32 | 0.72 |
| Horner | 32 | 0.67 |
| otimizada (redução + Horner) | 10 | 0.30 |

A recorrência é ~5× mais rápida que a ingênua para o mesmo erro, e a redução de argumento reduz os termos necessários de 32 para 10, além de dar erro uniforme em todo o intervalo. Os patamares no gráfico (~$10^{-13}$ e ~$10^{-16}$) são o limite de precisão do `float`.

## Arquivos

| arquivo | conteúdo |
|---|---|
| `src/taylor.py` | derivadas, as 4 implementações e a escolha de N (matemática pura) |
| `src/simulador.py` | interface interativa com matplotlib, só chama o `taylor.py` |
| `src/benchmark.py` | gera os gráficos e tabelas estáticos de `resultados/` |
| `src/serie_taylor_x_exp_x.ipynb` | notebook com derivadas, série, escolha de N, código, tabela e gráficos já executados |
| `resultados/` | PNGs e tabelas geradas pelo benchmark, com [`README.md`](resultados/README.md) explicando cada um |
| `requirements.txt` | dependências (numpy, matplotlib) |

## Referências

- Resto de Lagrange e série de Maclaurin: material da disciplina de Cálculo II.
- Redução de argumento para $e^x$: técnica clássica de bibliotecas matemáticas (ex.: descrita em _Elementary Functions_, J.-M. Muller). **Conferir e ajustar as referências que o grupo realmente consultou.**
