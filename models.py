"""Modelo de domínio do RentSmart (R.M Imóveis) - Programação Orientada a Objetos."""
import csv
import io
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP


def dinheiro(valor) -> Decimal:
    """Arredonda para 2 casas (centavos)."""
    return Decimal(valor).quantize(Decimal("0.01"), ROUND_HALF_UP)


def brl(valor) -> str:
    """Formata no padrão brasileiro: 1.234,56."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- Imóveis
class Imovel(ABC):
    """Classe base abstrata: todo imóvel tem aluguel-base e gera seus itens de cobrança."""
    NOME = ""
    ALUGUEL_BASE = Decimal("0")

    def itens(self) -> list:
        """Lista de (descrição, valor) que compõem o aluguel antes do desconto."""
        return [(f"Aluguel-base ({self.NOME})", self.ALUGUEL_BASE)]

    def desconto(self, subtotal: Decimal):
        """Por padrão não há desconto. Retorna (descrição, valor) ou None."""
        return None

    @property
    def aluguel_bruto(self) -> Decimal:
        return sum((v for _, v in self.itens()), Decimal("0"))

    @property
    def aluguel_mensal(self) -> Decimal:
        d = self.desconto(self.aluguel_bruto)
        return dinheiro(self.aluguel_bruto - (d[1] if d else 0))

    @abstractmethod
    def descricao(self) -> str: ...


class ImovelResidencial(Imovel):
    """Casas e apartamentos: 1 ou 2 quartos e vaga de garagem opcional."""
    ADICIONAL_2_QUARTOS = Decimal("0")
    VAGA_GARAGEM = Decimal("300")

    def __init__(self, quartos: int, garagem: bool):
        if quartos not in (1, 2):
            raise ValueError("Quartos deve ser 1 ou 2.")
        self.quartos, self.garagem = quartos, garagem

    def itens(self):
        lista = super().itens()
        if self.quartos == 2:
            lista.append(("Adicional de 2 quartos", self.ADICIONAL_2_QUARTOS))
        if self.garagem:
            lista.append(("Vaga de garagem", self.VAGA_GARAGEM))
        return lista

    def descricao(self):
        g = "com garagem" if self.garagem else "sem garagem"
        return f"{self.NOME}, {self.quartos} quarto(s), {g}"


class Apartamento(ImovelResidencial):
    NOME = "Apartamento"
    ALUGUEL_BASE = Decimal("700")
    ADICIONAL_2_QUARTOS = Decimal("200")
    DESCONTO_SEM_CRIANCAS = Decimal("0.05")

    def __init__(self, quartos, garagem, tem_criancas: bool):
        super().__init__(quartos, garagem)
        self.tem_criancas = tem_criancas

    def desconto(self, subtotal):
        if not self.tem_criancas:  # 5% após aplicar os adicionais
            return ("Desconto de 5% (sem crianças)", dinheiro(subtotal * self.DESCONTO_SEM_CRIANCAS))
        return None


class Casa(ImovelResidencial):
    NOME = "Casa"
    ALUGUEL_BASE = Decimal("900")
    ADICIONAL_2_QUARTOS = Decimal("250")


class Estudio(Imovel):
    """Estúdio: pacote de 2 vagas (R$ 250) + R$ 60 por vaga adicional."""
    NOME = "Estúdio"
    ALUGUEL_BASE = Decimal("1200")
    PACOTE_VAGAS, VAGAS_PACOTE = Decimal("250"), 2
    VAGA_EXTRA = Decimal("60")

    def __init__(self, vagas: int):
        if vagas != 0 and vagas < self.VAGAS_PACOTE:
            raise ValueError("Estúdio: informe 0 vagas ou, no mínimo, 2 (pacote inicial).")
        self.vagas = vagas

    def itens(self):
        lista = super().itens()
        if self.vagas:
            lista.append((f"Pacote de {self.VAGAS_PACOTE} vagas", self.PACOTE_VAGAS))
            extras = self.vagas - self.VAGAS_PACOTE
            if extras:
                lista.append((f"{extras} vaga(s) adicional(is) x R$ 60,00", self.VAGA_EXTRA * extras))
        return lista

    def descricao(self):
        return f"{self.NOME}, {self.vagas} vaga(s)"


def criar_imovel(dados: dict) -> Imovel:
    """Fábrica: valida a entrada e devolve o objeto Imovel adequado."""
    tipo = dados.get("tipo")
    try:
        if tipo == "apartamento":
            return Apartamento(int(dados["quartos"]), bool(dados["garagem"]), bool(dados["criancas"]))
        if tipo == "casa":
            return Casa(int(dados["quartos"]), bool(dados["garagem"]))
        if tipo == "estudio":
            return Estudio(int(dados["vagas"]))
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(str(e) if isinstance(e, ValueError) and e.args else "Dados inválidos.")
    raise ValueError("Tipo de imóvel inválido.")


# ------------------------------------------------------- Taxa e orçamento
class TaxaContratual:
    VALOR = Decimal("2000")
    MAX_PARCELAS = 5

    def __init__(self, parcelas: int):
        if not 1 <= parcelas <= self.MAX_PARCELAS:
            raise ValueError("Parcelas da taxa deve ser entre 1 e 5.")
        self.parcelas = parcelas

    def valores(self) -> list:
        base = dinheiro(self.VALOR / self.parcelas)
        lista = [base] * self.parcelas
        lista[-1] = self.VALOR - base * (self.parcelas - 1)  # ajuste de centavos
        return lista


class Orcamento:
    def __init__(self, imovel: Imovel, taxa: TaxaContratual):
        self.imovel, self.taxa = imovel, taxa

    def resumo(self) -> dict:
        i = self.imovel
        d = i.desconto(i.aluguel_bruto)
        return {
            "descricao": i.descricao(),
            "itens": [(n, v) for n, v in i.itens()],
            "subtotal": i.aluguel_bruto,
            "desconto": d,
            "aluguel_mensal": i.aluguel_mensal,
            "taxa_total": self.taxa.VALOR,
            "taxa_parcelas": self.taxa.parcelas,
            "taxa_parcela": self.taxa.valores()[0],
        }


class Projecao:
    """Projeção financeira dos 12 primeiros meses (aluguel + parcelas da taxa)."""
    MESES = 12

    def __init__(self, orcamento: Orcamento):
        self.orc = orcamento

    def linhas(self) -> list:
        aluguel, parcelas = self.orc.imovel.aluguel_mensal, self.orc.taxa.valores()
        out, acumulado = [], Decimal("0")
        for m in range(1, self.MESES + 1):
            taxa = parcelas[m - 1] if m <= len(parcelas) else Decimal("0")
            total = aluguel + taxa
            acumulado += total
            out.append((m, aluguel, taxa, total, acumulado))
        return out

    def para_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(["Mes", "Aluguel (R$)", "Parcela taxa contratual (R$)", "Total do mes (R$)", "Acumulado (R$)"])
        for m, *valores in self.linhas():
            w.writerow([m] + [brl(v) for v in valores])
        return buf.getvalue()

    def salvar(self, caminho: str):
        with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
            f.write(self.para_csv())
