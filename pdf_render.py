"""Gera PDF de verdade a partir do HTML de impressão, usando o Chrome headless.

Por que Chrome e não uma biblioteca: o template de impressão já existe e usa
grid/flex. Qualquer conversor mais simples renderiza diferente do que o João vê
na tela. O Chrome imprime exatamente igual.
"""

import os
import re
import shutil
import tempfile
import subprocess

CHROME = os.environ.get('CHROME_BIN') or shutil.which('google-chrome') \
    or shutil.which('chromium') or shutil.which('chromium-browser')

TIMEOUT = int(os.environ.get('PDF_TIMEOUT', '60'))


def disponivel():
    return bool(CHROME)


def html_para_pdf(html):
    """Recebe o HTML pronto e devolve os bytes do PDF."""
    if not CHROME:
        raise RuntimeError('Chrome/Chromium não encontrado no servidor')

    tmp = tempfile.mkdtemp(prefix='pdfdoc-')
    try:
        entrada = os.path.join(tmp, 'doc.html')
        saida = os.path.join(tmp, 'doc.pdf')
        with open(entrada, 'w', encoding='utf-8') as f:
            f.write(html)

        r = subprocess.run([
            CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
            '--no-pdf-header-footer', '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=1500',
            f'--user-data-dir={os.path.join(tmp, "perfil")}',
            f'--print-to-pdf={saida}', 'file://' + entrada,
        ], capture_output=True, text=True, timeout=TIMEOUT)

        if not os.path.exists(saida):
            raise RuntimeError((r.stderr or r.stdout or 'chrome falhou')[-400:])
        with open(saida, 'rb') as f:
            return f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pdf_para_png(pdf_bytes, pagina=1, dpi=150):
    """Converte uma página do PDF em PNG. Serve pro botão de copiar imagem:
    o navegador só deixa colar image/png no WhatsApp, PDF não vai."""
    if not shutil.which('pdftoppm'):
        raise RuntimeError('pdftoppm não instalado no servidor')
    tmp = tempfile.mkdtemp(prefix='pdfpng-')
    try:
        origem = os.path.join(tmp, 'e.pdf')
        with open(origem, 'wb') as f:
            f.write(pdf_bytes)
        base = os.path.join(tmp, 'pag')
        subprocess.run(['pdftoppm', '-png', '-r', str(dpi),
                        '-f', str(pagina), '-l', str(pagina),
                        '-singlefile', origem, base],
                       capture_output=True, timeout=TIMEOUT, check=True)
        with open(base + '.png', 'rb') as f:
            return f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def contar_paginas(pdf_bytes):
    m = re.findall(rb'/Type\s*/Page[^s]', pdf_bytes)
    return max(1, len(m))
