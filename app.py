"""Servidor local do RentSmart. Execute: python app.py  e abra http://localhost:8000"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from models import Orcamento, Projecao, TaxaContratual, brl, criar_imovel

PASTA = os.path.dirname(os.path.abspath(__file__))
CSV_SAIDA = os.path.join(PASTA, "projecao_12_meses.csv")


def gerar_orcamento(dados: dict) -> dict:
    orc = Orcamento(criar_imovel(dados), TaxaContratual(int(dados.get("parcelas", 1))))
    proj = Projecao(orc)
    proj.salvar(CSV_SAIDA)
    r = orc.resumo()
    return {
        "descricao": r["descricao"],
        "itens": [[n, brl(v)] for n, v in r["itens"]],
        "subtotal": brl(r["subtotal"]),
        "desconto": [r["desconto"][0], brl(r["desconto"][1])] if r["desconto"] else None,
        "aluguel_mensal": brl(r["aluguel_mensal"]),
        "taxa_total": brl(r["taxa_total"]),
        "taxa_parcelas": r["taxa_parcelas"],
        "taxa_parcela": brl(r["taxa_parcela"]),
        "projecao": [[m] + [brl(v) for v in vals] for m, *vals in proj.linhas()],
        "csv": proj.para_csv(),
    }


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, codigo, corpo: bytes, tipo="application/json"):
        self.send_response(codigo)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            for caminho in (os.path.join(PASTA, "static", "index.html"), os.path.join(PASTA, "index.html")):
                if os.path.exists(caminho):
                    with open(caminho, "rb") as f:
                        return self._enviar(200, f.read(), "text/html")
            self._enviar(404, "index.html não encontrado. Coloque-o na pasta 'static' ao lado do app.py.".encode(), "text/plain")
        else:
            self._enviar(404, b'{"erro":"Nao encontrado"}')

    def do_POST(self):
        if self.path != "/api/orcamento":
            return self._enviar(404, b'{"erro":"Nao encontrado"}')
        try:
            tam = int(self.headers.get("Content-Length", 0))
            dados = json.loads(self.rfile.read(tam) or b"{}")
            self._enviar(200, json.dumps(gerar_orcamento(dados)).encode())
        except (ValueError, KeyError) as e:
            self._enviar(400, json.dumps({"erro": str(e)}).encode())
        except Exception as e:  # nunca devolver HTML de erro para o front end
            self._enviar(500, json.dumps({"erro": f"Erro interno: {e}"}).encode())

    def do_OPTIONS(self):
        self._enviar(204, b"")


if __name__ == "__main__":
    try:
        servidor = HTTPServer(("localhost", 8000), Handler)
    except OSError:
        raise SystemExit("A porta 8000 está em uso. Feche o outro servidor (ou Live Server) e tente de novo.")
    print("RentSmart rodando em http://localhost:8000  (Ctrl+C para sair)")
    servidor.serve_forever()
