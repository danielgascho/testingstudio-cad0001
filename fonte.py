"""Identidade do objeto de estudo; o modelo suporta esta versão, não fontes arbitrários."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re


CAMINHO_FONTE = Path(__file__).resolve().with_name('cad0001_item_calculo.txt')
HASH_REFERENCIA = 'ce12d94b9666f87e23fadd5218705e4c0146616f5eb831e6bf832bb3cd42f070'
EVIDENCIA = 'Execução do modelo Python do original; sem execução nativa Informix-4GL'


def hash_conteudo(codigo):
    """Normaliza somente quebras de linha para permitir checkout Git em Windows/Linux."""
    return sha256(codigo.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')).hexdigest()


def modelo_compativel(codigo):
    return hash_conteudo(codigo) == HASH_REFERENCIA


@dataclass(frozen=True)
class Fonte:
    codigo: str
    nome: str

    @property
    def sha256(self):
        return hash_conteudo(self.codigo)

    @property
    def decimal(self):
        funcao = re.search(r'FUNCTION cad0001_calcula_valor\(.*?END FUNCTION', self.codigo, re.S)
        tipos = re.findall(r'DECIMAL\((\d+),\s*(\d+)\)', funcao.group() if funcao else '')
        if len(tipos) != 4 or len(set(tipos)) != 1:
            raise ValueError('A função deve declarar três parâmetros e um resultado com o mesmo DECIMAL(p,s).')
        return tuple(map(int, tipos[0]))

    @property
    def epsilon(self):
        return Decimal(1).scaleb(-self.decimal[1])

    @property
    def maximo(self):
        precisao, escala = self.decimal
        return Decimal(10) ** (precisao - escala) - self.epsilon


def ler_fonte():
    return Fonte(CAMINHO_FONTE.read_text(encoding='utf-8'), CAMINHO_FONTE.name)


def exigir_referencia(fonte):
    if not modelo_compativel(fonte.codigo):
        raise ValueError('O fonte foi alterado. O modelo instrumentado corresponde à versão original identificada por SHA-256.')
