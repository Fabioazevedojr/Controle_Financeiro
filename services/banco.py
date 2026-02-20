import sqlite3
from pathlib import Path

# Caminho absoluto até a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminho absoluto do banco de dados
DB_PATH = BASE_DIR / "database" / "controle_financeiro.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def autenticar_usuario(email, senha):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # gera hash da senha digitada (MD5)
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()


    cursor.execute("""
        SELECT id_usuario, nome, email, admin
        FROM usuarios
        WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
          AND senha_hash = ?
    """, (email, senha_hash))

    user = cursor.fetchone()
    conn.close()
    return user

def criar_tabelas():
    """Cria as tabelas do sistema se não existirem"""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            ativo INTEGER DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
            ativo INTEGER DEFAULT 1
        );
    """)

    # Tabela de lançamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id_lancamento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_categoria INTEGER NOT NULL,
            data DATE NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
            FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria)
        );
    """)

    conn.commit()
    conn.close()

def inserir_categorias_padrao():
    conn = conectar()
    cursor = conn.cursor()

    categorias = [
        ("Salário", "ENTRADA"),
        ("Freelance", "ENTRADA"),
        ("Outros ganhos", "ENTRADA"),

        ("Alimentação", "SAIDA"),
        ("Aluguel", "SAIDA"),
        ("Transporte", "SAIDA"),
        ("Lazer", "SAIDA"),
        ("Saúde", "SAIDA"),
        ("Educação", "SAIDA"),
        ("Outros gastos", "SAIDA"),
    ]

    for nome, tipo in categorias:
        cursor.execute("""
            INSERT OR IGNORE INTO categorias (nome, tipo)
            VALUES (?, ?)
        """, (nome, tipo))

    conn.commit()
    conn.close()

import hashlib


def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def criar_usuario_inicial():
    conn = conectar()
    cursor = conn.cursor()

    nome = "Admin"
    email = "admin@email.com"
    senha = "123456"  # depois você troca
    senha_hash = gerar_hash_senha(senha)

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash)
        VALUES (?, ?, ?)
    """, (nome, email, senha_hash))

    conn.commit()
    conn.close()

import sqlite3

DB_NAME = "controle_financeiro.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

# ==============================
# CRUD CATEGORIAS
# ==============================

def listar_categorias(id_usuario):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_categoria, nome, tipo
        FROM categorias
        WHERE id_usuario = ?
        ORDER BY nome
    """, (id_usuario,))

    categorias = cursor.fetchall()
    conn.close()
    return categorias


def adicionar_categoria(nome, tipo, id_usuario):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO categorias (nome, tipo, id_usuario)
        VALUES (?, ?, ?)
    """, (nome.strip(), tipo, id_usuario))

    conn.commit()
    conn.close()


def excluir_categoria(id_categoria):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM categorias
        WHERE id_categoria = ?
    """, (id_categoria,))

    conn.commit()
    conn.close()


def atualizar_categoria(id_categoria, nome, tipo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE categorias
        SET nome = ?, tipo = ?
        WHERE id_categoria = ?
    """, (nome.strip(), tipo, id_categoria))

    conn.commit()
    conn.close()

# ==============================
# CRUD LANÇAMENTOS
# ==============================

def listar_lancamentos(id_usuario):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.id_lancamento,
               l.data,
               l.valor,
               l.descricao,
               c.nome AS categoria,
               c.tipo
        FROM lancamentos l
        JOIN categorias c ON l.id_categoria = c.id_categoria
        WHERE l.id_usuario = ?
        ORDER BY l.data DESC
    """, (id_usuario,))

    dados = cursor.fetchall()
    conn.close()
    return dados


def adicionar_lancamento(id_usuario, id_categoria, data, valor, descricao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO lancamentos (id_usuario, id_categoria, data, valor, descricao)
        VALUES (?, ?, ?, ?, ?)
    """, (id_usuario, id_categoria, data, valor, descricao))

    conn.commit()
    conn.close()


def excluir_lancamento(id_lancamento):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM lancamentos
        WHERE id_lancamento = ?
    """, (id_lancamento,))

    conn.commit()
    conn.close()

# ==============================
# DASHBOARD
# ==============================

def resumo_financeiro(id_usuario, data_inicio=None, data_fim=None):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            c.tipo,
            SUM(l.valor) AS total
        FROM lancamentos l
        JOIN categorias c ON l.id_categoria = c.id_categoria
        WHERE l.id_usuario = ?
    """

    params = [id_usuario]

    if data_inicio and data_fim:
        query += " AND l.data BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])

    query += " GROUP BY c.tipo"

    cursor.execute(query, params)
    resultados = cursor.fetchall()

    conn.close()

    resumo = {"Receita": 0, "Despesa": 0}

    for r in resultados:
        resumo[r["tipo"]] = r["total"] or 0

    return resumo